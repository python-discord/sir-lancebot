# hacktoberbot
A community project for [Hacktoberfest 2018](https://hacktoberfest.digitalocean.com). A Discord bot primarily designed to help teach Python learners from the PythonDiscord community how to contribute to open source.

You can find our community by going to https://discord.gg/python

## Motivations
We know it can be difficult to get into the whole open source thing at first. To help out, we've decided to start a little community project during hacktober that you can all choose to contribute to if you're finding the event a little overwhelming, or if you're new to this whole thing and just want someone to hold your hand at first.

## Commands

!repository - Links to this repository

### Git
!Git - Links to getting started with Git page
!Git.commit - An example commit command

### Halloween Facts
Random halloween facts are posted regularly.  
!hallofact - Show the last posted Halloween fact

## Getting started

If you are new to this you will find it far easier using PyCharm:

### With PyCharm

First things first, what is PyCharm?  
PyCharm is a Python IDE(integrated development environment) that is used to make python development quicker and easier overall.  
So now your going to need to download it [here](https://www.jetbrains.com/pycharm/).

#### 1. Fork
Ok, now you have got PyCharm downloading you are going to want to fork this project and find its git URL. To fork scroll to the top of the page and press this button.
![](https://i.imgur.com/Saf9pgJ.png)
Then when you new forked repository loads you are going to want to get the Git Url by clicking the green `clone or download` button and then the copy link button as seen below:
![](https://i.imgur.com/o6kuQcZ.png)
#### 2. Clone
Now that you have done that you are going to want to load up Pycharm and you'll get something like this without the left sidebar:
![](https://i.imgur.com/xiGERvR.png)
You going to want to click Check Out from Version `Control->Git` and you'll get a popup like the one below:
![](https://i.imgur.com/d4U6Iw7.png)
Now paste your link in, test the connection and hit `clone`. You now have a copy of your repository to work with and it should setup your Pipenv automatically.
#### 3. Bot
Now we have setup our repository we need somewhere to test out bot.
You'll need to make a new discord server:
![](https://i.imgur.com/49gBlQI.png)
We need to make the applicaiton for our bot... navigate over to [discordapp.com/developers](https://discordapp.com/developers) and hit new application
![](https://i.imgur.com/UIeGPju.png)
Now we have our discord application you'll want to name your bot as below:
![](https://i.imgur.com/odTWSMV.png)
To actually make the bot hit `Bot->Add Bot->Yes, do It!` as below:
![](https://i.imgur.com/frAUbTZ.png)
Copy that Token and put to somewhere for safe keeping.
![](https://i.imgur.com/oEpIqND.png)
Now to add that robot to out new discord server we need to generate an OAuth2 Url to do so navigate to the OAuth2 tab, Scroll to the OAUTH2 URL GENERATOR section, click the `Bot` checkbox in the scope section and finally hit the `administrator` checkbox in the newly formed Bot Permissions section.
![](https://i.imgur.com/I2XzYPj.png)
Copy and paste the link into your browser and follow the instructions to add the bot to your server - ensure it is the server you have just created.
#### 4. Run Configurations
Go back to PyCharm and you should have something a bit like below, Your going to want to hit the `Add Configuration` button in the top right.
![](https://i.imgur.com/nLpDfQO.png)
We are going to want to choose a python config as below:
![](https://i.imgur.com/9FgCuP1.png)
The first setting we need to change is script path as below (the start script may have changed from bot.py so be sure to click the right one
![](https://i.imgur.com/napKLar.png)
Now we need to add an enviroment variable - what this will do is allow us to set a value without it affact the main repository.
To do this click the folder icon to the right of the text, then on the new window the plus icon. Now name the var `HACKTOBERBOT_TOKEN` and give the value the token we kept for safe keeping earilier.
![](https://i.imgur.com/nZFWNaQ.png)
Now hit apply on that window and your ready to get going!
#### 5. Git in PyCharm
As we work on our project we are going to want to make commits. Commits are effectively a list of changes you made to the pervious version. To make one first hit the green tick in the top right
![](https://i.imgur.com/BCiisvN.png)
1. Select the files you wish to commit
2. Write a brief description of what your commit is
3. See the actual changes you commit does here (you can also turn some of them off or on if you wish)
4. Hit commit

![](https://i.imgur.com/xA5ga4C.png)
Now once you have made a few commits and are happy with your changes you are going to want to push them back to your fork.
There are three ways of doing this.
1. Using the VSC Menu `VSC->Git->Push`
2. Using the VSC popup <code>alt-\`->Push</code>
3. A shortcut: `ctrl+shift+K`

You should get a menu like below:
1. List of commits
2. List of changed files
3. Hit Push to send to fork!

![](https://i.imgur.com/xA5ga4C.png)
#### 6. Pull Requests (PR or PRs)
Goto https://github.com/discord-python/hacktoberbot/pulls and the green New Pull Request button!
![](https://i.imgur.com/fB4a2wQ.png)
Now you should hit `Compare across forks` then on the third dropdown select your fork (it will be `your username/hacktoberbot`) then hit Create Pull request.
1[](https://i.imgur.com/N2X9A9v.png)
Now to tell other people what your PR does
1. Title - be concise and informative
2. Description - write what the PR changes as well as what issues it relates to
3. Hit `Create pull request`
![](https://i.imgur.com/OjKYdsL.png)

#### 7. Wait & further reading
At this point your PR will either be accepted or a maintainer might request some changes.

So you can read up some more on [https://try.github.io](Git), [https://www.jetbrains.com/help/pycharm/quick-start-guide.html](PyCharm) or you might want to learn more about Python and discord: [https://discordpy.readthedocs.io/en/rewrite/](discord.py rewrite)


### Without PyCharm
The process above can be completed without PyCharm however it will be necessary to learn how to use Git, Pipenv and Environment variables.

You can find tutorials for the above below:
- Git: [try.github](http://try.github.io/)
- Pipenv [Pipenv.readthedocs](https://pipenv.readthedocs.io)
- Environment Variables: [youtube](https://youtu.be/bEroNNzqlF4?t=27)
