# SeasonalBot 

[![Build Status](https://dev.azure.com/python-discord/Python%20Discord/_apis/build/status/Seasonal%20Bot%20(Mainline))](https://dev.azure.com/python-discord/Python%20Discord/_build/latest?definitionId=3)
[![Discord](https://discordapp.com/api/guilds/267624335836053506/embed.png)](https://discord.gg/2B963hn)

A Discord bot for the Python Discord community which changes with the seasons, and provides useful event features.

You can find our community by going to https://discord.gg/python

## Motivations

We know it can be difficult to get into the whole open source thing at first. To help out, we started the HacktoberBot community project during [Hacktoberfest 2018](https://hacktoberfest.digitalocean.com) to help introduce and encourage members to participate in contributing to open source, providing a calmer and helpful environment for those who want to be part of it.

This later evolved into a bot that runs all year, providing season-appropriate functionality and issues that beginners can work on.

## Getting started

Please ensure you read the [contributing guidelines](CONTRIBUTING.md) in full.

If you are new to this you may find it easier to use PyCharm. [What is PyCharm?](#what-is-pycharm)

1. [Fork the Project](#fork-the-project)
2. [Clone & Install Packages](#clone--install-packages)
3. [Test Server](#test-server)
4. [Bot Account](#bot-account)
5. [Configuration](#configuration)
6. [Working with Git](#working-with-git)
7. [Pull Requests (PRs)](#pull-requests-prs)
8. [Further Reading](#further-reading)

### What is PyCharm?  

PyCharm is a Python IDE (integrated development environment) that is used to make python development quicker and easier.  

Our instruction include PyCharm specific steps for those who have it, so you're welcome to give it a go if you haven't tried it before.

You can download PyCharm for free [here](https://www.jetbrains.com/pycharm/).

### Requirements

- [Python 3.7](https://www.python.org/downloads/)
- [Pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv)
- Git
  - [Windows Installer](https://git-scm.com/download/win)
  - [MacOS Installer](https://sourceforge.net/projects/git-osx-installer/files/) or `brew install git`

### Fork the Project

To fork this project, press the Fork button at the top of the [repository page](https://github.com/python-discord/seasonalbot):

![](https://i.imgur.com/gPfSW8j.png)

In your new forked repository, copy the git url by clicking the green `clone or download` button and then the copy link button:

![](https://i.imgur.com/o6kuQcZ.png)

### Clone & Install Packages

#### With PyCharm:

Load up PyCharm and click `Check Out from Version Control` -> `Git`:

![](https://i.imgur.com/ND7Z5rN.png)

Test the URL with `Test` first and then click `Clone`.

![](https://i.imgur.com/gJkwHA0.png)

Note: PyCharm automatically detects the Pipfile in the project and sets up your packages for you.

#### With console:

Open a console at the directory you want your project to be in and use the git clone command to copy the project files from your fork repository:

```bash
git clone https://github.com/yourusername/seasonalbot.git
```

Change your console directory to be within the new project folder (should be named `seasonalbot` usually) and run the pipenv sync command to install and setup your environment.
```bash
cd seasonalbot
pipenv sync --dev
```

### Test Server

Create a test discord server if you haven't got one already:

![](https://i.imgur.com/49gBlQIl.png)

In your test server, ensure you have the following:
 - `#announcements` channel
 - `#dev-logs` channel
 - `admins` role
 - A channel to test your commands in.

### Bot Account

Go to the [Discord Developers Portal](https://discordapp.com/developers/applications/) and click the `New Application` button, enter the new bot name and click `Create`:

![](https://i.imgur.com/q5wlDPs.png)

In your new application, go to the `Bot` tab, click `Add Bot` and confirm `Yes, do it!`:

![](https://i.imgur.com/PxlscgF.png)

Change your bot's `Public Bot` setting off so only you can invite it, save, and then get your token with the `Copy` button:

![](https://i.imgur.com/EM3NIiB.png)

Save your token somewhere safe so we can put it in the project settings later.

In the `General Information` tab, grab the Client ID:

![](https://i.imgur.com/pG7Ix3n.png)

Add the Client ID to the following invite url and visit it in your browser to invite the bot to your new test server:
```
https://discordapp.com/api/oauth2/authorize?client_id=CLIENT_ID_HERE&permissions=8&scope=bot
```

Optionally, you can generate your own invite url in the `OAuth` tab, after selecting `bot` as the Scope.

### Configuration

#### Environment Variables:

Create a `.env` file in your project root and copy the following text into it:
```
SEASONALBOT_DEBUG=True
SEASONALBOT_TOKEN=0
SEASONALBOT_GUILD=0
SEASONALBOT_ADMIN_ROLE_ID=0
CHANNEL_ANNOUNCEMENTS=0
CHANNEL_DEVLOG=0
```

Edit the variable values to match your own bot token that you put aside earlier, the ID of your Guild, the Announcements and Dev-logs channel IDs and the admin role ID. To get the role ID, you can make it mentionable, and send an escaped mention like `\@admin`:

![](https://i.imgur.com/qANC8jA.png)

Note: These are only the basic environment variables. Each season will likely have their own variables needing to set, so be sure to check out the respective seasonal setups that you're working on.

#### PyCharm Project Config:

Copy the contents of your `.env` file first.  
Click the `Add Configuration` button in the top right of the window.

![](https://i.imgur.com/Qj2RDwU.png)

In the Configuration Window do the following:
1. Click the plus on the top left and select `Python`.  
2. Add `bot` to the `Script path` input box.
5. Add `-m` to the `Interpreter options` input box.

![](https://i.imgur.com/3Cs05fg.png)

Click the folder icon for the `Environment variables` input box. In the new window, click the paste icon on the right side and click `OK`:

![](https://i.imgur.com/ET6gC3e.png)

Note: This should have your actual bot token and IDs as the values. If you copied the blank template from above and didn't update it, go back to do so first.

Click `OK` to save and close the Configuration window.

From now on, to run the bot you only need to click the `Run` button in the top right of PyCharm:

![](https://i.imgur.com/YmqnLqC.png)

#### In console:

Since we have the `.env` file in the project root, anytime we run Pipenv and it'll automatically load the environment variables present within.

To run the the bot, use:
```bash
pipenv run start
```

### Working with Git

Working with git can be intimidating at first, so feel free to ask for any help in the server.

For each push request you work on, you'll want to push your commits to a branch just for it in your repository. This keeps your `master` branch clean, so you can pull changes from the original repository without pulling the same commits you've already added to your fork.

Once you finish a push request, you can delete your branch, and pull the changes from the original repository into your master branch. With the master branch updated, you can now create a new branch to work on something else.

Note: You should never commit directly to the original repository's `master` branch. All additions to the `master` branch of the original repository **must** be put through a PR first.

#### Precommit Hook

Projects need to pass linting checks to be able to successfully build and pass as in push requests.  
Read [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

To install the precommit hook, which checks your code before commits are submitted, do the following:
```bash
pipenv run precommit
```

#### In PyCharm

The PyCharm interface has a set of Git actions on the top right section of your workspace:

![](https://i.imgur.com/1LsyMx9.png)

In order from left to right these are:
- Update
- Commit
- History
- Revert

As we work on our project we are going to want to make commits. Commits are effectively a log of changes you made over time.

Before making any commits, you should make the branch for the PR you're about to work on. At the bottom of the PyCharm workspace, you'll see the current git branch, which you can click to show a menu of actions. You can click `New Branch` to create a new one, and name it something short that references what the PR is to accomplish. Before making new branches, be sure you change to `master` and ensure it's up to date before creating a new branch.

![](https://i.imgur.com/A9zV4lF.png)

After making changes to the project files, you can commit by clicking the `Commit` button that's part of the git actions available on the top right of your workspace.

The flow of making a commit is as follows:

1. Select the files you wish to commit.
2. Write a brief description of what your commit is.
3. See the actual changes you commit does, and optionally tick/untick specific changes to only commit the changes you want.
4. Click `Commit`.

![](https://i.imgur.com/MvGQKT9.png)

To create a new branch, 

Once you have made a few commits and are ready to push them to your fork repository, you can do any of the following:
- Use the VSC Menu `VSC` -> `Git` -> `Push`
- Use the VSC popup `alt-\ ` -> `Push`
- Use the Push shortcut: `CTRL+SHIFT+K`

You should see a window listing commits and changed files.  
Click `Push` when you're ready and it'll submit the commits to your forked repository.

#### With console:

When you create a commit, you will either want to add certain files for that commit, or apply all changes to every file.

It's recommended to add only the files that you want to apply changes to before committing, rather than committing everything tracked. This brings more caution, and allows you to check first each file is relevant to the PR you're working on.

To only add certain files, you will need to do that first before committing:  
```bash
# create/use feature branch
git checkout some_new_feature

# stage a single file
git add my_file.py

# stage multiple files in one command
git add file_one.py file_two.py file_three.py

# stage all files in current directory
git add .

# remove a file from staging
git rm --cached wrong_file.py

# finally commit
git commit -m "commit message here"
```

If you're absolutely sure that the tracked changes are all within scope of your PR, you can try using the commit all command.  
To commit all changes across all tracked files, just use the `-a` flag:  
```bash
git commit -a -m "commit message here"
```

### Pull Requests (PRs)

Go to the [Pull requests](https://github.com/python-discord/seasonalbot/pulls) and click the green New Pull Request button:

![](https://i.imgur.com/fB4a2wQ.png)

Click `Compare across forks`.  
Change the `head fork` dropdown box to your fork (`your_username/seasonalbot`).  
Click `Create pull request`.

![](https://i.imgur.com/N2X9A9v.png)

In the PR details, put a concise and informative title.  
Write a description for the PR regarding the changes and any related issues.  
Ensure `Allow edits from maintainers.` has been ticked.  
Click `Create pull request`.

![](https://i.imgur.com/yMJVMNj.png)

A maintainer or other participants may comment or review your PR, and may suggest changes. Communicate in the PR ticket and try ensure you respond timely on any questions or feedback you might get to prevent a PR being marked stale.

After a successful review by a maintainer, the PR may be merged successfully, and the new feature will deploy to the live bot within 10 minutes usually.

### Further Reading

- [Git](https://try.github.io)
- [PyCharm](https://www.jetbrains.com/help/pycharm/quick-start-guide.html)
- [Pipenv](https://pipenv.readthedocs.io)
- [discord.py rewrite](https://discordpy.readthedocs.io/en/rewrite)
- [Environment Variables (youtube)](https://youtu.be/bEroNNzqlF4?t=27)
