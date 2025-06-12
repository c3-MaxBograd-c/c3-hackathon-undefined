/*
 * Copyright 2009-2025 C3 AI (www.c3.ai). All Rights Reserved.
 * Confidential and Proprietary C3 Materials.
 * This material, including without limitation any software, is the confidential trade secret and proprietary
 * information of C3 and its licensors. Reproduction, use and/or distribution of this material in any form is
 * strictly prohibited except as set forth in a written license agreement with C3 and/or its authorized distributors.
 * This material may be covered by one or more patents or pending patent applications.
 */

/**
 * The default `generatePackageSteps` step has the following customizations:
 * - Run test avoidance
 * - Queue codeAnalysisInit step
 * - Queue semanticVersionValidation step
 *
 * After the steps are queued, the Jarvis pipeline is as below:
 *
 *                            |---> UI bundling (pkg1) ---> test execution (pkg1) ... ---|
 * ... -> codeAnalysisInit ---|                                                          |--> buildSummary
 *                            |---> UI bundling (pkg2) ---> test execution (pkg2) ... ---|
 *
 * Note:
 * - The semanticVersionValidation step is a blocking step of the codeAnalysisInit step. The codeAnalysisInit step will
 * only start after the semanticVersionValidation step has completed.
 */
data = {
  name: 'generatePackageSteps',
  value: function (step) {
    function getTestStrategiesForAffectedPkgs(affectedPackages) {
      // [{ strategy: string, tests: [string] }]
      var testStrategiesString = Jarvis.buildConfigValue('testStrategies');
      var testStrategies = C3.Array.fromJsonString(testStrategiesString || '[]');

      if (!testStrategies || !affectedPackages.length) {
        return [];
      }

      var TEST_PATTERN =
        '((?!.*/disabled/).*/test/(py|py-.*|js|js-.*|notebook|ts|ts-.*)/.*test_.*\\.(py|js|json|ts|tsx))';
      var repositoryFiles = JarvisExecutor.Helper.fs().listFiles(repoPath, -1);

      /*
       * Look specifically for instances where the affected package name is bounded by `/` which would correspond
       * to a directory. This regex ensure no false positives are captured. For instance, `demandForecastingUI` would
       * match if the regex only searches for `demandForecasting`.
       */
      var affectedPackagesRegex = '/(' + affectedPackages.join('|') + ')/';
      var affectedPackageTestFiles = repositoryFiles.files.filter((file) => {
        return !!(file.url.match(affectedPackagesRegex) && file.url.match(TEST_PATTERN));
      });

      var strategiesForAffectedPackages = [];
      _.each(testStrategies, (testStrategy, idx) => {
        var testRegExps = testStrategy.tests;
        if (!testRegExps || !testRegExps.length) {
          return true;
        }

        var validTestRegExps = testRegExps.filter((testRegExp) => {
          var anyFile = affectedPackageTestFiles.findAny((file) => {
            return !!file.url.match(testRegExp);
          });
          return !!anyFile;
        });

        if (!validTestRegExps.length) {
          return true;
        }

        var updatedTestStrategy = C3.Map.fromJson(testStrategy).with('tests', validTestRegExps).toJson();
        strategiesForAffectedPackages.push(updatedTestStrategy);
      });

      return strategiesForAffectedPackages;
    }

    function getRepoPath(step) {
      var baseDirPath = JarvisExecutor.Helper.baseDirFor(step);
      var repoStash = step.jarvisBuild.stashFor('repository.zip');
      var pkgsPath = step.jarvisBuild.packagesPath;
      return JarvisExecutor.SourceControlManager.unstashRepo(repoStash, baseDirPath, pkgsPath);
    }

    var repoPath = getRepoPath(step);

    /*
     * Retrieve the package declarations from the repository stash. This will include downstream
     * repository packages.
     */
    function getRepositoryPkgDecls() {
      var pkgDeclPaths = JarvisExecutor.SourceControlManager.pkgPaths(repoPath);

      // Get all Pkg.Decl objects from repository
      return Array.from(
        pkgDeclPaths.map((pkgPath) => {
          return Pkg.Decl.fromJsonString(File.fromString(pkgPath).readString());
        })
      );
    }

    var pkgDecls = getRepositoryPkgDecls();

    /**
     * Recursive function to determine if `currentPackage` is affected by at least one package in `modifiedPackages`.
     */
    function hasDependencyOnModifiedPkg(modifiedPackages, dependencyGraph, currentPackage) {
      if (!dependencyGraph[currentPackage]) {
        return false;
      }

      if (modifiedPackages[currentPackage]) {
        return true;
      }

      var hasDependency = false;
      var currentPkgDeps = dependencyGraph[currentPackage];
      _.each(modifiedPackages, (modifiedPkg) => {
        if (currentPkgDeps.containsKey(modifiedPkg)) {
          hasDependency = true;
          return true;
        }
      });

      currentPkgDeps.keys().each((currentPkgDep) => {
        if (hasDependencyOnModifiedPkg(modifiedPackages, dependencyGraph, currentPkgDep)) {
          hasDependency = true;
          return true;
        }
      });
      return hasDependency;
    }

    /**
     * Function to determine the subset of `pkgDecls` that include at least one of packages in `modifiedPackages`
     * in their dependency chain.
     */
    function determineAffectedPkgs(modifiedPackages, pkgDecls) {
      // Build dependency graph of each package.
      var dependencyGraph = {};
      _.each(pkgDecls, (pkgDecl) => {
        var pkgName = pkgDecl.name;
        var dependencies = pkgDecl.dependencies;
        dependencyGraph[pkgName] = dependencies || {};
      });

      /*
       * Initialize affected packages with the modified packages. Determine affected packages by looping through
       * each defined package declaration and determining if they have a modified package in their dependency chain.
       */
      var affectedPkgs = Array.from(modifiedPackages);
      _.each(pkgDecls, (pkgDecl) => {
        var pkgName = pkgDecl.name;
        if (hasDependencyOnModifiedPkg(affectedPkgs, dependencyGraph, pkgName)) {
          affectedPkgs.push(pkgName);
        }
      });
      return affectedPkgs;
    }

    function testAvoidance(step) {
      var jarvisBuild = step.jarvisBuild;
      var testAvoidanceBranchRegex = Str.unquote(Jarvis.buildConfigValue('testAvoidanceBranchRegex'));
      var testAvoidanceMessage = '';

      // Boolean to indicate whether test avoidance should be run. True if branch matches `testAvoidanceBranchRegex`.
      var runTestAvoidance = jarvisBuild.branch.match(testAvoidanceBranchRegex);

      var modifiedPackages = new Set();

      // Only enable test avoidance for branch that match the test avoidance branch regex.
      if (runTestAvoidance) {
        var restApi = Jarvis.sourceControlRestApi();

        // Test avoidance is only possible with GitHub currently
        if (restApi.type().name() === 'GitHubRestApi') {
          var gitHub = restApi.restInst;

          // Set the default test avoidance default branch.
          var baseBranch = Jarvis.branchGroupConfigValue('defaultTestAvoidanceBranch');
          if (step.jarvisBuild.prUrl) {
            baseBranch = gitHub.pullRequest(restApi.orgWithSrcCtrlRepoName, step.jarvisBuild.prUrl.split('/').pop())
              .base.ref;
          }
          if (!baseBranch) {
            baseBranch = gitHub.repository(restApi.orgWithSrcCtrlRepoName).default_branch;
          }

          var compareResult = gitHub.compare(restApi.orgWithSrcCtrlRepoName, baseBranch, jarvisBuild.sha);
          var repoDir = jarvisBuild.packagesPath;

          // The comparison result will only show up to 300 files so test all packages if we reach this limit
          var fileLimit = 300;

          // Using the comparison result, collect the names of packages with modified files
          if (compareResult.files.length < fileLimit) {
            compareResult.files.each(function (file) {
              var filename = file.filename;
              if (filename.indexOf(repoDir) === 0) {
                var path = filename.replace(repoDir + '/', '');
                if (path.indexOf('/') > -1) {
                  modifiedPackages.add(path.split('/').shift());
                }
              }
            });
          } else {
            testAvoidanceMessage =
              'Test avoidance skipped because more than 300 files are different with the base branch: ' + baseBranch;
            return testAvoidanceMessage;
          }
        }

        if (modifiedPackages.size > 0) {
          // Set the packagesToInclude config value so that only affected packages will be built and tested
          var affectedPackages = determineAffectedPkgs(modifiedPackages, pkgDecls);
          Jarvis.setBuildConfigValue('packagesToInclude', JSON.stringify(affectedPackages));

          // Get test strategies for affected packages.
          var testStrategiesForAffectedPkgs = getTestStrategiesForAffectedPkgs(affectedPackages);
          Jarvis.setBuildConfigValue('testStrategies', Jsn.stringify(testStrategiesForAffectedPkgs));

          testAvoidanceMessage = [
            'Test avoidance identified the following package changes with base branch ' + baseBranch + ':',
            JSON.stringify(Array.from(modifiedPackages)),
            '',
            'The following affected packages will be built:',
            _.map(affectedPackages, (affectedPackage) => {
              return '- ' + affectedPackage;
            }).join('\\n'),
            '',
            'The test strategy was updated to:',
            testStrategiesForAffectedPkgs,
          ].join('\\n');
        } else {
          testAvoidanceMessage =
            'Test avoidance was not run because there were no package differences found with base branch: ' +
            baseBranch;
        }
      } else {
        testAvoidanceMessage =
          'Test avoidance was not run because branch ' +
          jarvisBuild.branch +
          ' did not match regex ' +
          testAvoidanceBranchRegex +
          '.';
      }

      // Store test avoidance-related metadata for reference in other steps and for debugging.
      var testAvoidanceReport = Jarvis.Report.make({
        data: {
          baseBranch: baseBranch,
          runTestAvoidance: runTestAvoidance,
          testAvoidanceMessage: testAvoidanceMessage,
          modifiedPackages: Array.from(modifiedPackages),
        },
        category: 'Test Avoidance',
        subcategory: 'Metadata',
      });
      Jarvis.fileReports([testAvoidanceReport]);

      return testAvoidanceMessage;
    }

    // Function to call a lambda in the `<env>/c3` context. This is required for all calls to the `Pkg.Store` API.
    function callLambdaInEnvContext(lambda) {
      return AnyType.unboxValue(C3.env().c3App().callJson('Lambda', 'call', Lambda.fromJsFunc(lambda)));
    }

    /**
     * Function to validate whether the provided list of packages have an upstream dependency on `jarvisBaseToolkit`.
     *
     * The `generatePackageSteps` step also schedules steps for code analysis initialization, code analysis runs and
     * code analysis summaries. The `codeAnalysisInit` step must use a package that has a dependency on
     * `jarvisBaseToolkit` to ensure the it has access to all the `jarvisBaseToolkit` APIs.
     *
     * @param {string[]} packageNames
     *          The list of packages to validate the `jarvisBaseToolkit` dependency for.
     * @returns {string[]}
     *          List of packages that are neither an upstream nor downstream dependency
     *          of `jarvisBaseToolkit`.
     */
    function getMissingBaseToolkitDependency(packageNames) {
      // Include `jarvisBaseToolkit` to handle scenario where `jarvisBaseToolkit` is being built.
      var baseCodeUpstreamDependencies = callLambdaInEnvContext(() => {
        return Pkg.Store.pkg('jarvisBaseToolkit').dependencyNames().toSet();
      });
      var pkgStoreJarvisBaseToolkitPkgs = callLambdaInEnvContext(() => {
        return Pkg.Store.dependentPkgNames('jarvisBaseToolkit').toSet();
      });

      var pkgsWithMissingBaseToolkitDependency = packageNames
        .toSet()
        .difference(C3.Set.fromJson(['jarvisBaseToolkit']))
        .difference(baseCodeUpstreamDependencies)
        .difference(pkgStoreJarvisBaseToolkitPkgs)
        .toArray('[string]');

      return {
        pkgsWithMissingBaseToolkitDependency: pkgsWithMissingBaseToolkitDependency,
        baseCodeUpstreamDependencies: baseCodeUpstreamDependencies,
      };
    }

    /**
     * Function to throw a validation error with an error message prompting the user to add an upstream dependency on
     * `baseCodeAnalyzer` to get a successful build. Should only be called if `pkgsWithMissingBaseToolkitDependency`
     * is non-empty.
     *
     * @param step
     *          The Jarvis step to throw the validation error for.
     * @param pkgsWithMissingBaseToolkitDependency
     *          The list of packages missing an upstream dependency on `baseCodeAnalyzer`.
     * @returns
     *         `Jarvis.Step.Result` with status set to ERROR and error message prompting user to add
     *         baseToolkit dependency.
     */
    function throwBaseCodeAnalyzerValidationError(step, pkgsWithMissingBaseToolkitDependency) {
      // Post a commit status directing the user to navigate to this step's logs in the Jarvis UI to see the error.
      var commitStatusMessage =
        'Build aborted due to missing dependencies. Please see the `generatePackageSteps` step for more information.';
      var restApi = Jarvis.sourceControlRestApi();
      if (restApi.type().name() === 'GitHubRestApi') {
        restApi.restInst.createCommitStatus(
          restApi.orgWithSrcCtrlRepoName,
          step.jarvisBuild.sha,
          'error',
          'C3 AI Code Analyzer',
          commitStatusMessage
        );
      }

      /*
       * Prompt to add dependency on `baseToolkit` which is the official released artifact (which in-turn includes)
       * `baseCodeAnalyzer` as an upstream dependency.
       */
      var pkgsWithMissingBaseToolkitDependencyString = [];
      pkgsWithMissingBaseToolkitDependency.each((packageName) => {
        pkgsWithMissingBaseToolkitDependencyString.push('- ' + packageName);
      });
      var errorMessage = [
        'The following packages in this build are missing a dependency on `baseToolkit`: ',
        pkgsWithMissingBaseToolkitDependencyString.join('\\n'),
        '',
        'Please add an implicit/explicit dependency on `baseToolkit` to each of these packages to run a successful build.',
      ].join('\\n');
      return Jarvis.Step.Result.builder()
        .step(step)
        .status(Jarvis.Step.Status.NON_RETRYABLE_ERROR)
        .error(errorMessage)
        .build();
    }

    function getBuildSummaryStep(step) {
      return Jarvis.accessData('JarvisService.Step', 'fetch', {
        filter: Filter.eq('jarvisBuild', step.jarvisBuild.id).and().eq('name', 'buildSummary'),
      }).objs.first().id;
    }

    var testAvoidanceOutputMessage = '';
    try {
      /*
       * Run test avoidance before the `generatePackageSteps` to ensure `packagesToInclude` includes
       * only affected packages.
       */
      testAvoidanceOutputMessage = testAvoidance(step);
    } catch (e) {
      // Queue step to surface instantiation error to the user.
      // eslint-disable-next-line no-redeclare
      var errorMessage =
        'Failed to run test avoidance steps because of the following error. ' +
        'Please reach out to ENG-X immediately.\\n' +
        e.toString();

      var testAvoidanceInstErrorStep = Jarvis.Step.builder()
        .id(step.jarvisBuild.id + '-testAvoidanceInstErrorStep')
        .name('c3standardsStepInstError')
        .input(step.input.with('errorMessage', errorMessage))
        .jarvisBuild(step.jarvisBuild)
        .build();
      Jarvis.addSteps([testAvoidanceInstErrorStep]);
    }

    // Run the `generatePackageSteps` package to queue UI bundling and test steps.
    var result = JarvisExecutor.Helper.generatePackageSteps(step);

    try {
      var packagesToInclude = C3.Array.fromJsonString(Jarvis.buildConfigValue('packagesToInclude'));
      var artifactsFilter = Filter.startsWith('id', step.jarvisBuild.id)
        .and()
        .eq('kind', ArtifactHub.ArtifactKind.LEGACY_PKG);

      /*
       * Query Artifact Hub for the full semantic versions of each package that was generated as part of
       * this build. We only fetch the legacy pkg artifacts to avoid fetching the same artifact multiple times.
       *
       * This filter doesn't respect the packagesToInclude build config because we want the full versions
       * of all built packages even if they weren't run due to test avoidance.
       */
      var buildArtifacts = ArtifactHub.availableVersions({ filter: artifactsFilter });
      var packageNameToSemanticVersionMap = buildArtifacts
        .toMap((artifact) => {
          return artifact.name;
        })
        .map((artifact) => {
          return artifact.semanticVersion;
        });

      var packageNames = packageNameToSemanticVersionMap.keys().collect();

      // If packagesToInclude is defined, only check those packages.
      if (packagesToInclude && packagesToInclude.length > 0) {
        packageNames = packageNames.filter((packageName) => {
          return packagesToInclude.contains(packageName);
        });
      }
      var baseToolkitDependencyMetadata = getMissingBaseToolkitDependency(packageNames);
      var pkgsWithMissingBaseToolkitDependency = baseToolkitDependencyMetadata.pkgsWithMissingBaseToolkitDependency;
      var baseCodeUpstreamDependencies = baseToolkitDependencyMetadata.baseCodeUpstreamDependencies;

      if (pkgsWithMissingBaseToolkitDependency.length) {
        return throwBaseCodeAnalyzerValidationError(step, pkgsWithMissingBaseToolkitDependency);
      }

      var codeAnalysisInitStepId = step.jarvisBuild.id + '-codeAnalysisInit';
      var topLevelCustomerPackage = Str.unquote(Jarvis.buildConfigValue('topLevelCustomerPackage'));
      if (topLevelCustomerPackage === 'null') {
        topLevelCustomerPackage = null;
      }

      var uiBundlingSteps = Jarvis.accessData('JarvisService.Step', 'fetch', {
        filter: Filter.eq('jarvisBuild', step.jarvisBuild.id)
          .and()
          .intersects('name', ['generateUiBundles', 'skippingUiBundling']),
      }).objs;

      var codeAnalysisInitStepInput;
      packageNames.each((packageName) => {
        /*
         * Store custom package name and artifact to run the code analysis summary step from.
         * For customer repositories from which we want to collect customization reports, the codeAnalysisSummary
         * step must use the configured `topLevelCustomerPackage` to run the analyze code APIs.
         */
        if (
          (!codeAnalysisInitStepInput || topLevelCustomerPackage === packageName) &&
          !baseCodeUpstreamDependencies.contains(packageName)
        ) {
          codeAnalysisInitStepInput = C3.Map.ofStrToAny(
            'pkgName',
            packageName,
            'customPkgName',
            packageName,
            'customPkgVersion',
            packageNameToSemanticVersionMap.get(packageName),
            'packageNameToSemanticVersionMap',
            packageNameToSemanticVersionMap,
            'baseCodeUpstreamDependencies',
            baseCodeUpstreamDependencies,
            'uiBundlingSteps',
            uiBundlingSteps
          );
        }
      });

      var buildSummaryStep = getBuildSummaryStep(step);
      var codeAnalysisInitStep = Jarvis.Step.make({
        id: codeAnalysisInitStepId,
        name: 'codeAnalysisInit',
        input: codeAnalysisInitStepInput,
        next: buildSummaryStep,
        maxRetries: 3,
      });

      // Add semantic version validation.
      var semanticVersionValidationStep = Jarvis.Step.make({
        name: 'semanticVersionValidation',
        input: C3.Map.fromJson({
          pkgDecls: _.map(pkgDecls, (pkgDecl) => {
            return pkgDecl.toJson();
          }),
        }),
        next: codeAnalysisInitStepId,
        maxRetries: 3,
      });

      Jarvis.addSteps([semanticVersionValidationStep, codeAnalysisInitStep]);
    } catch (e) {
      // Queue step to surface instantiation error to the user.
      // eslint-disable-next-line no-redeclare
      var errorMessage =
        'Failed to instantiate code analysis initialization step because of the following error. ' +
        'Please reach out to ENG-X immediately.\\n' +
        e.toString();

      var codeAnalysisInstErrorStep = Jarvis.Step.builder()
        .id(step.jarvisBuild.id + '-codeAnalysisInstErrorStep')
        .name('c3standardsStepInstError')
        .input(step.input.with('errorMessage', errorMessage))
        .jarvisBuild(step.jarvisBuild)
        .build();
      Jarvis.addSteps([codeAnalysisInstErrorStep]);
    }

    // Add the error message for test avoidance along with the messages returned by Jarvis.generatePackageSteps.
    var stepOutputMessage = [testAvoidanceOutputMessage, '', result.error || ''].join('\\n');
    return Jarvis.Step.Result.make(result).withError(stepOutputMessage);
  },
};
