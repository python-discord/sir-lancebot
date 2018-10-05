# hacktoberbot
A community project for [Hacktoberfest 2018](https://hacktoberfest.digitalocean.com). A Discord bot primarily designed to help teach Python learners from the PythonDiscord community how to contribute to open source.

You can find our community by going to https://discord.gg/python

## Motivations
We know it can be difficult to get into the whole open source thing at first. To help out, we've decided to start a little community project during hacktober that you can all choose to contribute to if you're finding the event a little overwhelming, or if you're new to this whole thing and just want someone to hold your hand at first.

*Lemon*

## Commands

### repository
Alias: project
A command to send the hacktoberbot github project

### git
Alias: github
A command that sends a getting started with Git page

### git.commit
Sends a sample first commit

## Getting started

If you are new to this you will find it far easier using PyCharm:

### With PyCharm

First things first, what is PyCharm?  
PyCharm is a Python IDE(integrated development environment) that is used to make python development quicker and easier overall.  
So now your going to need to download it [here](https://www.jetbrains.com/pycharm/).

#### 1. Fork
Ok, now you have got PyCharm downloading you are going to want to fork this project and find its git URL. To fork scroll to the top of the page and press this button.
![](https://i.imgur.com/Saf9pgJ.png)
then when you new forked repository loads you are going to want to get the Git Url by clicking the green clone or download button and then the copy link button as seen below:
![](https://i.imgur.com/o6kuQcZ.png)
#### 2. Clone
Now that you have done that you are going to want to load up Pycharm and you'll get something like this without the left sidebar:
![](https://i.imgur.com/xiGERvR.png)
You going to want to click Check Out from Version Control->Git and you'll get a popup like the one below:
![](https://i.imgur.com/d4U6Iw7.png)
Now paste your link in, test the connection and hit clone. You now have a copy of your repository to work with and it should setup your Pipenv automatically.
#### 3. Bot
Now we have setup our repository we need somewhere to test out bot.
You'll need to make a new discord server:
![](https://i.imgur.com/49gBlQI.png)
We need to make the applicaiton for our bot... navigate over to [discordapp.com/developers](https://discordapp.com/developers) and hit new application
![](https://i.imgur.com/UIeGPju.png)
Now we have our discord application you'll want to name your bot as below:
![](https://i.imgur.com/odTWSMV.png)
To actually make the bot hit Bot->Add Bot->Yes, do It! as below:
![](https://i.imgur.com/frAUbTZ.png)
Copy that Token and put to somewhere for safe keeping.
![](https://i.imgur.com/oEpIqND.png)
Now to add that robot to out new discord server we need to generate an OAuth2 Url to do so navigate to the OAuth2 tab, Scrollto the OAUTH2 URL GENERATOR section, click the Bot checkbox in the scope section and finally hit the administrator checkboxin the newly formed Bot Permissions section.
![](https://i.imgur.com/I2XzYPj.png)
Copy and paste the link into your browser and follow the instructions to add the bot to your server - ensure it is the server you have just created.
#### 4. Run Configurations
Go back to PyCharm and you should have something a bit like below, Your going to want to hit the Add Configuration button in the top right.
![](https://i.imgur.com/nLpDfQO.png)
We are going to want to choose a python config as below:
![](https://i.imgur.com/9FgCuP1.png)
