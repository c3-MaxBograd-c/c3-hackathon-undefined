/*
 * Copyright 2009-2025 C3 AI (www.c3.ai). All Rights Reserved.
 * Confidential and Proprietary C3 Materials.
 * This material, including without limitation any software, is the confidential trade secret and proprietary
 * information of C3 and its licensors. Reproduction, use and/or distribution of this material in any form is
 * strictly prohibited except as set forth in a written license agreement with C3 and/or its authorized distributors.
 * This material may be covered by one or more patents or pending patent applications.
 */

data = {
  configValues: {
    /**
     * By default, the code analyzer posts a maximum of 10 inline comments on a pull request.
     * The maximum comment count can be configured to be any number greater than 0.
     */
    maxCodeAnalyzerCommentCount: 10,

    /**
     * By default, the code analyzer does not push the results of the code analysis to a centralized repository
     * for code analytics. Setting this value to true pushes the changes to a centralized repository for
     * observability.
     *
     * If this configuration is turned on for customer repositories, the `topLevelCustomerPackage` and the
     * `customerPackages` configurations HAVE to be provided.
     */
    reportResultsToCodeAnalytics: false,

    /**
     * By default, customization analysis is not performed in Jarvis builds. Customer repositories in the c3-e
     * organization can send encrypted usage analytics to the centralized code analytics repository for analysis
     * that could help improve the base product.
     *
     * Set this configuration to point to the name of the top-level package in the customer repository that is
     * ultimately deployed to prod. If this configuration is non-null, please ensure the `customerPackages`
     * configuration is configured appropriately and `reportResultsToCodeAnalytics` is set to true.
     */
    topLevelCustomerPackage: null,

    /**
     * By default, customization analysis is not performed in Jarvis builds. Customer repositories in the c3-e
     * organization can send encrypted usage analytics to the centralized code analytics repository for analysis
     * that could help improve the base product.
     *
     * Set this configuration to point to the list of all packages defined in customer repositories. This should
     * include the `topLevelCustomerPackage` and any packages that might have been defined in other customer
     * repositories on which this repository belongs. If this configuration is non-null, please ensure the
     * `topLevelCustomerPackage` configuration is configured appropriately and `reportResultsToCodeAnalytics`
     * is set to true.
     */
    customerPackages: [],

    /**
     * Code analysis should behave slightly differently depending on whether the repository belongs to a base
     * application or a customer application. This configuration should be set to the following:
     *
     *   - `base-app` for base applications (default)
     *   - `customer` for customer applications
     */
    codeAnalysisConfig: 'base-app',

    /**
     * Store the processedResults in a centralized code analytics repository.
     * Only store results for the mainline branches.
     *
     * Each element in the array is a regular expression used to match the branch name. The entire branch name
     * is matched against the regular expression. If the branch name matches any of the regular expressions,
     * its processedResults will be stored. When escaping characters, you must use two backslashes.
     *
     * ┌─────────────┬──────────────────────┬──────────┐
     * │ Regex       │ Branch               │ Matches? │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ release     │ release              │ Yes      │
     * │             │ release/v10.0        │ No       │
     * │             │ hotfix/release/v10.0 │ No       │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ release/v.* │ release              │ No       │
     * │             │ release/v10.0        │ Yes      │
     * │             │ hotfix/release/v10.0 │ No       │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ .*release.* │ release              │ Yes      │
     * │             │ release/v10.0        │ Yes      │
     * │             │ hotfix/release/v10.0 │ Yes      │
     * └─────────────┴──────────────────────┴──────────┘
     *
     * By default, code analysis results are reported for the following branches:
     *
     *   - develop
     *   - release
     *   - release/v*.* (e.g., release/v10.0)
     *   - master
     *   - support/v*.* (e.g., support/v10.0)
     */
    storeResultBranches: ['develop', 'release', 'release/v[0-9]+\\.[0-9]+', 'master', 'support/v[0-9]+\\.[0-9]+'],

    /**
     * **BETA**
     *
     * By default, documentation artifacts are not generated automatically for a repository. This should only be set to
     * true for all base repositories.
     *
     * Generated documentation artifacts are automatically registered to the upstream documentation artifact hub. Builds
     * that generate documentation must use one of the following pre-release tags, or an error will be thrown:
     *
     *   - `dev`
     *   - `rc`
     *   - `stable`
     *   - `support`
     *
     * @see docArtifactGenerationBranches
     */
    generateDocArtifacts: false,

    /**
     * **BETA**
     *
     * > Only applies when `generateDocArtifacts` is enabled.
     *
     * The list of branches to generate documentation artifacts for automatically.
     *
     * Each element in the array is a regular expression used to match the branch name. The entire branch name
     * is matched against the regular expression. If the branch name matches any of the regular expressions,
     * documentation artifacts will be generated. When escaping characters, you must use two backslashes.
     *
     * ```plaintext
     * ┌─────────────┬──────────────────────┬──────────┐
     * │ Regex       │ Branch               │ Matches? │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ release     │ release              │ Yes      │
     * │             │ release/v10.0        │ No       │
     * │             │ hotfix/release/v10.0 │ No       │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ release/v.* │ release              │ No       │
     * │             │ release/v10.0        │ Yes      │
     * │             │ hotfix/release/v10.0 │ No       │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ .*release.* │ release              │ Yes      │
     * │             │ release/v10.0        │ Yes      │
     * │             │ hotfix/release/v10.0 │ Yes      │
     * └─────────────┴──────────────────────┴──────────┘
     * ```
     *
     * By default, documentation artifacts are automatically generated for the following branches:
     *
     *   - develop
     *   - release
     *   - release/v*.* (e.g., release/v10.0)
     *   - master
     *   - support/v*.* (e.g., support/v10.0)
     */
    docArtifactGenerationBranches: [],

    /**
     * **DEPRECATED**: This configuration only applies to documentation generation for the legacy developer portal.
     *                 In the future, this will be removed in favor of `generateDocArtifacts`.
     *
     * By default, documentation artifacts are not generated automatically for a repository. This should only be set to
     * true for all base repositories.
     */
    generateDocumentationArtifacts: false,

    /**
     * **DEPRECATED**: This configuration can be used to generate documentation for the legacy developer portal.
     *                 In the future, this will be removed in favor of `docArtifactGenerationBranches`, which
     *                 configures which branches generate documentation for the new doc site.
     *
     * The list of branches to generate legacy documentation artifacts for automatically.
     *
     * Each element in the array is a regular expression used to match the branch name. The entire branch name
     * is matched against the regular expression. If the branch name matches any of the regular expressions,
     * legacy documentation artifacts will be generated. When escaping characters, you must use two backslashes.
     *
     * ```plaintext
     * ┌─────────────┬──────────────────────┬──────────┐
     * │ Regex       │ Branch               │ Matches? │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ release     │ release              │ Yes      │
     * │             │ release/v10.0        │ No       │
     * │             │ hotfix/release/v10.0 │ No       │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ release/v.* │ release              │ No       │
     * │             │ release/v10.0        │ Yes      │
     * │             │ hotfix/release/v10.0 │ No       │
     * ├─────────────┼──────────────────────┼──────────┤
     * │ .*release.* │ release              │ Yes      │
     * │             │ release/v10.0        │ Yes      │
     * │             │ hotfix/release/v10.0 │ Yes      │
     * └─────────────┴──────────────────────┴──────────┘
     * ```
     *
     * By default, legacy documentation artifacts are automatically generated for the following branches:
     *
     *   - release
     *   - release/v*.* (e.g., release/v10.0)
     *   - master
     *   - support/v*.* (e.g., support/v10.0)
     */
    documentationArtifactGenerationBranches: [
      'release',
      'release/v[0-9]+\\.[0-9]+',
      'master',
      'support/v[0-9]+\\.[0-9]+',
    ],

    /**
     * **DEPRECATED**: This configuration only applies to documentation generation for the legacy developer portal.
     *                 This will be removed in the future.
     *
     * The map from the top-level package for a C3 application and its corresponding release management identifier.
     * These values are used for constructing the C3 semantic versions to be used for exporting the documentation
     * artifacts.
     *
     * For example, say the Reliability application (root package of `reliability`) is on version 16.0.0 and uses
     * the release management identifier `rel`. Setting this value to { 'reliability': 'rel' } would export the
     * documentation as `rel16.0.0-p8.4.0`.
     */
    documentationApplicationIdentifiers: {},

    /**
     * The regular expression used to determine if test avoidance should be enabled for a particular branch.
     * By default, only `feature/` and `task/` branches are enabled.
     *
     * When updating this regex, please use the following command to validate in the static console. A non-null value
     * should be expected as the output when testing this feature.
     *
     * ```js
     * Js.exec(`
     *   var testAvoidanceBranchRegex = '(^feature/.*)|(^task/.*)';
     *   var branch = 'feature/engx/ENGR-123';
     *   branch.match(testAvoidanceBranchRegex);
     * `);
     * ```
     */
    testAvoidanceBranchRegex: '(^feature/.*)|(^task/.*)',
  },
  secretValues: {
    /**
     * By default, the code analyzer uses the token of the user who created the Jarvis branch configuration
     * in Studio. An increased usage of this token could trigger secondary rate limits and it is suggested
     * that at least one backup token be provided to allow the C3 AI Code Analyzer to perform automated
     * reviews without interruptions.
     *
     * IMPORTANT: Please do not set the value here. Edit your branch group configuration in the Studio UI or run
     * the following in your `jarvisservice` application to set your tokens:
     *
     * ```js
     * Jarvis.setBranchGroupSecretValue(
     *   '<your_branchGroupId>',
     *   'backupSourceControlTokens',
     *   JSON.stringify(['<your_tokens>'])
     * );
     * ```
     */
    backupSourceControlTokens: JSON.stringify([]),
  },
};
