/*
 * Copyright 2009-2025 C3 AI (www.c3.ai). All Rights Reserved.
 * Confidential and Proprietary C3 Materials.
 * This material, including without limitation any software, is the confidential trade secret and proprietary
 * information of C3 and its licensors. Reproduction, use and/or distribution of this material in any form is
 * strictly prohibited except as set forth in a written license agreement with C3 and/or its authorized distributors.
 * This material may be covered by one or more patents or pending patent applications.
 */

data = {
  name: 'buildSummary',
  value: function (step) {
    function shouldSkipCodeAnalysis(step) {
      var numCodeAnalysisReports = Jarvis.accessData('JarvisService.Report', 'fetchCount', {
        filter: Filter.eq('jarvisBuild', step.jarvisBuild.id)
          .and()
          .eq('category', 'Code Analysis')
          .and()
          .eq('subcategory', 'Package Results'),
      }).count;

      /*
       * As of version 11 of baseToolkit, code analysis is supported for branches with code coverage
       * enabled. Only skip code analysis for branches with code coverage enabled if the baseToolkit
       * version is less than 11, in which case all codeAnalysis steps will have been placeholders,
       * so no reports will have been generated.
       *
       * This check should be removed in 8.6 as all users of c3standards on 8.6 must be on at least
       * baseToolkit version 11, so codeAnalysisSummary should always be triggered.
       */
      return numCodeAnalysisReports <= 0;
    }

    // Return immediately if code analysis should be skipped.
    if (shouldSkipCodeAnalysis(step)) {
      return JarvisExecutor.Helper.buildSummary(step);
    }

    /**
     * Helper function to get the execution times for code analysis steps.
     */
    function getCodeAnalysisStepDurations(step) {
      var codeAnalysisSteps =
        Jarvis.accessData('JarvisService.Step', 'fetch', {
          filter: Filter.eq('jarvisBuild', step.jarvisBuild.id).and().eq('name', 'codeAnalysis'),
        }).objs || [];

      var stepsWithDuration = codeAnalysisSteps.map(function (codeAnalysisStep) {
        var durationString = Jarvis.WithStateHistory.make({
          state: codeAnalysisStep.state,
          stateHistory: codeAnalysisStep.stateHistory,
        }).duration();
        var duration = Duration.fromString(durationString);
        return {
          id: codeAnalysisStep.id,
          durationString: durationString,
          duration: duration,
        };
      });
      return stepsWithDuration;
    }

    /**
     * Helper function to get the latest processed report for the base branch in the repository.
     * This function fetches the last 5 most recently completed builds for the base branch to account for
     * non-"success" final states and picks the processed results report for the most recently completed build.
     */
    function getBaseBranchResultsInfo(baseBranch, repositoryUrl) {
      var baseBranchBuilds = Jarvis.accessData('JarvisService.Build', 'fetch', {
        filter: Filter.intersects('branch', baseBranch)
          .and()
          .eq('state', Jarvis.State.DONE)
          .and()
          .eq('repositoryUrl', repositoryUrl),
        include: 'id',
        order: 'descending(meta.created)',
        limit: 5,
      });

      var baseBranchResults = [];

      // Only attempt to get the processed results if there are any builds corresponding to the base branch.
      if (baseBranchBuilds.count) {
        var baseBranchBuildIds = _.map(baseBranchBuilds.objs || [], (build) => {
          return build.id;
        });
        var codeAnalysisReports = Jarvis.accessData('JarvisService.Report', 'fetch', {
          filter: Filter.intersects('jarvisBuild', baseBranchBuildIds)
            .and()
            .eq('category', 'Code Analysis')
            .and()
            .eq('subcategory', 'Processed Results'),
          include: 'data',
          order: 'descending(meta.created)',
        }).objs;

        baseBranchResults =
          codeAnalysisReports && codeAnalysisReports[0] && codeAnalysisReports[0].data.codeAnalysisResults;
      }

      return {
        baseBranch: baseBranch,
        baseBranchResults: baseBranchResults,
      };
    }

    function stashReports(step) {
      var codeAnalysisReports =
        Jarvis.accessData('JarvisService.Report', 'fetch', {
          filter: Filter.intersects('jarvisBuild', step.jarvisBuild.id)
            .and()
            .eq('category', 'Code Analysis')
            .and()
            .eq('subcategory', 'Package Results'),
          include: 'data',
        }).objs || [];

      var results = codeAnalysisReports
        .filter((childReport) => {
          return childReport.data.status === 'success';
        })
        .map((childReport) => {
          return childReport.data.result;
        })
        .toJsonString();

      var codeAnalysisResultsStash = step.jarvisBuild.stashFor('codeAnalysisResults');
      codeAnalysisResultsStash.writeString(results);
    }

    try {
      // Stash reports to be retrieved in the `codeAnalysisSummary` step.
      stashReports(step);

      var codeAnalysisStash = step.jarvisBuild.stashFor('codeAnalysisMetadata');
      var codeAnalysisMetadata = JSON.parse(codeAnalysisStash.readString());

      var nextSteps = [];

      var codeAnalysisStepsWithDuration = getCodeAnalysisStepDurations(step);

      // Get base branch results to get comparison values.
      var baseBranchResultsInfo = getBaseBranchResultsInfo(
        codeAnalysisMetadata.baseBranch,
        step.jarvisBuild.repositoryUrl
      );

      // Add a step to notify users of the code analysis results.
      var reportResultsToCodeAnalytics = Jarvis.buildConfigValue('reportResultsToCodeAnalytics');
      var codeAnalysisSummaryStep = Jarvis.Step.builder()
        .id(Uuid.create())
        .name('codeAnalysisSummary')
        .input(
          step.input
            .with('baseBranch', codeAnalysisMetadata.baseBranch)
            .with('baseBranchResults', baseBranchResultsInfo.baseBranchResults)
            .with('codeAnalysisStepsWithDuration', codeAnalysisStepsWithDuration)
            .with('customPkgName', codeAnalysisMetadata.packageName)
            .with('customPkgVersion', codeAnalysisMetadata.semanticVersion)
            .with('reportResultsToCodeAnalytics', Str.toBool(reportResultsToCodeAnalytics))
        )
        .next(step.next)
        .jarvisBuild(step.jarvisBuild)
        .maxRetries(3)
        .build();

      nextSteps.push(codeAnalysisSummaryStep);
      Jarvis.addSteps(nextSteps);
    } catch (e) {
      /**
       * Update status check to notify of error and transition to a final-state if the code above fails.
       *
       * We need to resolve these in the custom lambda since doing so through the logic in `baseCodeAnalyzer`
       * would require us to go over the same steps as those that would have failed in the `try` block.
       */
      var restApi = Jarvis.sourceControlRestApi();
      if (restApi.type().name() === 'GitHubRestApi') {
        restApi.restInst.createCommitStatus(
          restApi.orgWithSrcCtrlRepoName,
          step.jarvisBuild.sha,
          'error',
          'C3 AI Code Analyzer',
          'There was an error in reporting your code analysis results.'
        );
      }

      // Add the code analysis instantiation error step to surface the error to the user.
      var errorMessage =
        'Failed to instantiate code analysis summary step because of the following error.\\n' + e.toString();
      var codeAnalysisInstErrorStep = Jarvis.Step.builder()
        .id(step.jarvisBuild.id + '-codeAnalysisSummaryInstError')
        .name('c3standardsStepInstError')
        .input(step.input.with('errorMessage', errorMessage))
        .jarvisBuild(step.jarvisBuild)
        .maxRetries(3)
        .build();
      Jarvis.addSteps([codeAnalysisInstErrorStep]);
    }

    // This custom step will override the buildSummary step. First, we need to run the build summary as usual.
    return JarvisExecutor.Helper.buildSummary(step);
  },
};
