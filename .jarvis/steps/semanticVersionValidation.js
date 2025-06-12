/*
 * Copyright 2009-2025 C3 AI (www.c3.ai). All Rights Reserved.
 * Confidential and Proprietary C3 Materials.
 * This material, including without limitation any software, is the confidential trade secret and proprietary
 * information of C3 and its licensors. Reproduction, use and/or distribution of this material in any form is
 * strictly prohibited except as set forth in a written license agreement with C3 and/or its authorized distributors.
 * This material may be covered by one or more patents or pending patent applications.
 */

data = {
  name: 'semanticVersionValidation',
  value: function (step) {
    var pkgDecls = step.input.pkgDecls;
    var repositoryPkgNames = pkgDecls
      .map((packageDecl) => {
        return packageDecl.name;
      })
      .toSet();

    /*
     * In multi-repository builds, we should only consider packages that are in the repository for which the build is
     * running. Skip packages that are not in the list of `currentRepositoryPkgs`.
     */
    function getCurrentRepositoryPkgDecls(step, pkgDecls) {
      var reports =
        Jarvis.accessData('JarvisService.Report', 'fetch', {
          filter: Filter.eq('jarvisBuild', step.jarvisBuild.id)
            .and()
            .eq('category', 'Code Analysis')
            .and()
            .eq('subcategory', 'Current Repository Packages'),
          include: 'data',
        }).objs || [];

      /*
       * If no reports were filed for 'Current Repository Packages', no multi-repository builds were run.
       * Return all locally available pkgDecls in that scenario.
       */
      if (!reports.length) {
        return pkgDecls;
      }

      var currentRepositoryPkgs = C3.Set.fromJson(reports[0].data.currentRepoPkgs);
      return _.filter(pkgDecls, (pkgDecl) => {
        return currentRepositoryPkgs.contains(pkgDecl.name);
      });
    }

    var currentRepositoryPkgDecls = getCurrentRepositoryPkgDecls(step, pkgDecls);
    var semanticVersions = _.map(currentRepositoryPkgDecls, 'version');

    function printPackageList(pkgDecls) {
      return _.map(pkgDecls, (pkgDecl) => {
        return '- ' + pkgDecl.name;
      }).join('\\n');
    }

    // Throw an error when packages have a missing semantic version.
    var packagesWithMissingVersion = _.filter(currentRepositoryPkgDecls, (pkgDecl) => {
      return pkgDecl.version == null;
    });
    if (packagesWithMissingVersion.length) {
      var missingPkgVersionErrorMessage = [
        'The following packages are missing a semantic version declared in their .c3pkg.json file.',
        'Please set the semantic version to same value as other packages in this repository:',
        printPackageList(packagesWithMissingVersion),
      ].join('\\n');
      return Jarvis.Step.Result.builder()
        .error(missingPkgVersionErrorMessage)
        .step(step)
        .status(Jarvis.Step.Status.ERROR)
        .build();
    }

    // Throw an error when packages have different semantic versions.
    var uniqueSemanticVersions = _.uniq(semanticVersions);
    if (uniqueSemanticVersions.length > 1) {
      var packagesGroupedByVersion = _.groupBy(currentRepositoryPkgDecls, 'version');
      var printedSemanticVersions = _.map(_.toPairs(packagesGroupedByVersion), (packageVersionGroup) => {
        var semanticVersion = packageVersionGroup[0];
        var versionPkgDecls = packageVersionGroup[1];
        return ['', 'Version ' + semanticVersion, printPackageList(versionPkgDecls)].join('\\n');
      }).join('\\n');

      var uniqSemVerErrorMessage = [
        'All packages in the repository must have the same semantic version.',
        'Please set the semantic version of the following packages to the same version:',
        printedSemanticVersions,
      ].join('\\n');
      return Jarvis.Step.Result.builder()
        .error(uniqSemVerErrorMessage)
        .step(step)
        .status(Jarvis.Step.Status.ERROR)
        .build();
    }

    /*
     * Throw an error when any dependency as defined as "*" instead of a specific version or if the package belongs
     * to the same repository but does not have latest version.
     */
    var repositorySemanticVersion = uniqueSemanticVersions[0];
    var incorrectDependencySemanticVersions = [];
    var incorrectDependencyVersionPatch = [];
    var VERSION_REGEX = /^[0-9]+(\.[0-9]+)?$/;
    _.each(currentRepositoryPkgDecls, (pkgDecl) => {
      var packageName = pkgDecl.name;
      var dependencies = pkgDecl.dependencies ? C3.Map.fromJson(pkgDecl.dependencies) : C3.Map.fromJson({});
      dependencies.each((depVersion, depPackage) => {
        // Prompt users to use a specific version instead of '*' or a range like ^8.4 or >=8.4.0 <8.5.0
        if (!SemanticVersion.isValid(depVersion.trim())) {
          incorrectDependencySemanticVersions.push(
            '- ' + depPackage + ' in ' + packageName + '.c3pkg.json must have specific semantic version'
          );
        }

        if (repositoryPkgNames.contains(depPackage) && depVersion !== repositorySemanticVersion) {
          incorrectDependencySemanticVersions.push(
            '- ' +
              depPackage +
              ' in ' +
              packageName +
              '.c3pkg.json must match the latest version: ' +
              repositorySemanticVersion
          );
        }

        /*
         * Throw an error when a semantic version of a dependency package outside
         * the repo has a `patch` version. (Example: if the dependency is `"pkgA": "1.0.1"`).
         */
        if (!repositoryPkgNames.contains(depPackage) && !VERSION_REGEX.test(depVersion)) {
          incorrectDependencyVersionPatch.push(
            '- External dependency `' + depPackage + '` must specify only a `major` or `major.minor` version.'
          );
        }
      });
    });

    var result;
    if (incorrectDependencySemanticVersions.length) {
      var incorrectDepErrorMessage = [
        'Please set the following dependency semantic version of packages:',
        incorrectDependencySemanticVersions.join('\\n'),
      ].join('\\n');
      result = Jarvis.Step.Result.builder()
        .error(incorrectDepErrorMessage)
        .step(step)
        .status(Jarvis.Step.Status.ERROR)
        .build();
      return result;
    }

    if (incorrectDependencyVersionPatch.length) {
      var incorrectDepPatchMessage = [
        "Dependencies on packages outside the current repository shouldn't have a patch version:",
        incorrectDependencyVersionPatch.join('\\n'),
      ].join('\\n');
      result = Jarvis.Step.Result.make({
        error: incorrectDepPatchMessage,
        step: step,
        status: Jarvis.Step.Status.ERROR,
      });
      return result;
    }

    return Jarvis.Step.Result.builder().step(step).status(Jarvis.Step.Status.SUCCESS).build();
  },
};
