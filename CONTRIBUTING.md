# How to contribute to the Graph-Onedrive package

Thank you for considering contributing to the package!


## Support questions

Please don't use the issue tracker for this. The issue tracker is a tool to address bugs and feature requests in the code source itself.

Support is not provided for this package.


## Reporting issues

When [reporting an issue][1], please include the following information:

* Describe what you expected to happen;
* If possible, include a [minimal reproducible example](https://stackoverflow.com/help/minimal-reproducible-example) to help identify the issue. This also helps check that the issue is not with your own code;
* Describe what actually happened. Include the full trace-back if there was an exception;
* List your Python and package versions. If possible, check if this issue is already fixed in the latest releases or the latest code in the repository.


## Feature requests and feedback

The best way to send feedback is to [file an issue][1].

If you are proposing a feature:

* Explain in detail how it would work;
* Keep the scope as narrow as possible, to make it easier to implement;
* Remember that this is a volunteer-driven project, and that code contributions are welcome.


## Documentation improvements

Documentation can always be improved, whether as part of the official docs or in doc-strings.
Please first discuss any deviations from the current documentation formats already in use in the package.


## Testing

Testing your code is fairly simple using the tests already set up.

1. Install the Tox: `pip install -U tox >= 4.0`
2. Ensure that you are within the graph-onedrive directory
3. Enter `tox` into the console
4. A testing environment should be created automatically, and tests commence

You are of course welcome to add additional tests within the tests directory.


## Submitting patches

If there is not an open issue for what you want to submit, the preference is for you to open one for discussion before working on a pull request. You can work on any issue that doesn't have an open PR linked to it or a maintainer assigned to it. These show up in the sidebar. There is no need to ask if you can work on an issue that interests you.
It is suggested that you fork to a branch named after the issue (ie not `main`) to simplify merge/rebase.

When submitting your patch, please ensure that you:

1. Test your code;
2. Include type annotations;
3. Update any relevant docs pages and doc-strings;
4. Add an entry in `CHANGES.md`;
5. Ideally run [pre-commit](https://pre-commit.com), and correct any issues.



[1]: <https://github.com/dariobauer/graph-onedrive/issues> "GitHub issues"
