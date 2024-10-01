https://doc.qt.io/qtforpython-6/quickstart.html

# Option 1: Create virtual environment
With a virtual environment, all installed packages are installed only to the project.  It is recommended to use protection.
1) In the root of the project, open a terminal and execute `python -m venv env`
2) Every time you want to test your code, you need to activate the virtual environment:
	`env\Scripts\activate.bat`
	Or you can run `activate_env.bat`

# Option 2: Don't create virtual environment
1) Don't use protection

# Finally:
From the root of the project (after activating the env if applicable):
`pip install -r requirements.txt`

You can test by running the `pyside6_test.py` script in `src/`
