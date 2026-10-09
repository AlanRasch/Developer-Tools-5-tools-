Developer tools (5 of them) The five tools are:

	1	Dependency Security Triage Agent. Scans a project’s packages for known vulnerabilities, works out which ones actually affect the code (not just the ones listed in the package file), and suggests the smallest safe upgrade. Supply-chain attacks and vulnerable packages are a constant concern, and most alerts are noise, so a tool that separates real risks from false alarms is valuable.
	2	Pull Request Summarizer and Reviewer. Reads a pull request’s diff and writes a plain-language summary, lists risky changes (such as removed error handling or new database queries), and flags missing tests. It saves reviewers time, which is often the bottleneck on a team.
	3	Documentation Drift Detector. Compares the README and docstrings with the actual code and reports where they disagree, such as a renamed option or a removed command. Outdated documentation is one of the most common complaints from new developers.
	4	Commit Message and Changelog Writer. Turns the staged changes into a clear commit message that follows a team’s convention, and builds release notes from commits since the last tag. It is quick to adopt, and most developers would use it daily.
	5	Local Developer Environment Doctor. Checks a machine for the right Python or Node version, required tools, environment variables, and ports already in use, then explains how to fix each problem. Setting up a project on a new laptop, especially on Windows, is a frequent source of wasted hours.

  Things to check:
	•	Dependency Triage’s live lookup was not tested. This environment has no internet access, so the tests use a fake database. Run it once on a machine with internet to confirm.
	•	Windows and macOS were not tested directly. The code uses only standard Python libraries, and the commands are written for both systems, but please run each tool once on each system.
	•	The PR Reviewer and Commit Writer use simple rules. They catch common cases well, but they do not understand your code’s design. Their READMEs say so.
	•	The AI options are optional. Only the PR Reviewer’s summary uses Claude, and only when you pass with-claude. 
