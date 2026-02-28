# Lab 4 Report: **Issue Resolution**

## Project Description

### Project Name: **Sir Lancebot**

### URL: https://github.com/python-discordsir-lancebot

### One or two sentences describing it:

Sir Lancebot is an open-source Discord bot written in Python and maintained by the Python Discord community. On the project, contributors can implement new commands and features, or fix issues.

## Onboarding experience

### Did you choose a new project or continue on the previous one? If you changed the project, how did your experience differ from before?

We decided to select a new project because the remaining open issues in the mockito project were very complex to resolve. Therefore, we chose to siwtch to `Sir Lancebot`.

The experience of selecting an issue in this new project was more satisfactory and straightforward. We chose one that the whole team found particularly interesting. The issue was clearly described, and provide to us more flexibility in terms of implementation and decision-making.



## Effort spent For each team member, how much time was spent in
1. plenary discussions/meetings;
2. discussions within parts of the group;
3. reading documentation;
4. configuration and setup;
5. analyzing code/output;
6. writing documentation;
7. writing code;
8. running code?

For setting up tools and libraries (step 4), enumerate all dependencies you took care of and where you spent your time, if that time exceeds 30 minutes.

## Overview of issue(s) and work done.

### Title: Kenken command #989
### URL: https://github.com/python-discord/sir-lancebot/issues/989 (link to the original issue, should it be the issue to the pullrequest or the fork instead?)
### Summary in one or two sentences Scope (functionality and code affected).
We created a Mathdoku game command for the Sir Lancebot Discord bot. We only created new files in the sir-lancebot repository and did not change any existing files.

## Requirements for the new feature or requirements affected by functionality being refactored

- **FR-01 - Help Command Exposure:**
The bot shall expose a `help` entry under the command group `.Mathdoku` for running **mathdoku**.

- **FR-02 - Start Game Command:**
The command `.md start`shall start a new valid **mathdoku** game session.

- **FR-03 - Grid Size:**
The `.md start` command shall accept an optional grid size parameter.

- **FR-04 - Independent Game Sessions:**
Each game session shall maintain an independent board state.

- **FR-05 - Hint Message Publication:**
After starting a game, the bot publish a hint message and automatically attach a lightbulb emoji reaction to that message.

- **FR-06 - Hint Cooldown Mechanism:**
There shall be a cooldown period of 180 seconds between consecutive hint requests.

- **FR-07 - Board Representation:**
The board shall be internally represented as an indexable matrix structure, accessible by row and column coordinates.

- **FR-08 - Cell Data Model:**
Each cell in the board shall store its row and column coordinates, associated block, current guessed value, and correct solution value.

- **FR-09 - Board Parsing Validation:**
The board parser shall ignore any invalid configuration that violates the mathdoku rules.

- **FR-10 - Block Data Model:**
Each block shall store a unique id, a mathematical operation, and a target result number.

- **FR-11 - Input Request Handling:**
The game shall prompt the player to provide input moves during gameplay. The bot must clearly indicate when user input is expected.

- **FR-12 - Leave command:**
The game shall provide a command allowing users to leave an active game session.

- **FR-13 - Invalid Input Notification:**
The bot shall notify the user whenever an invalid input is detected.

- **FR-14 - Inactivity Timeout:**
The game session shall automatically terminate after a defined period of user inactivity.

- **FR-15 - Win Condition Validation:**
The game shall validate winning conditions by checking both the Latin square properly and correct block constraint satisfaction.

- **FR-16 - Error Identification:**
The game shall identify incorrect cells or blocks.

- **FR-17 - Visual Board Representation:**
The board shall be visually represented as an image showing grid structure and blocking coloring.

- **FR-18 - Hint Reaction Trigger:**
The bot shall trigger the hint logic when a user reacts with the lightbulb emoji on the hint message.

- **FR-19 - Hint Contect Logic:**
A hint shall return the first empty cell in teh board and reveal its correct value.

- **FR-20 - Cooldown Feedback:**
The bot shall notify the user of the remaining cooldown time in seconds.

- **FR-21 - No Available Hint Notification:**
The bot shall notify the user that no hints are available if all cells in the board are filled.

Optional (point 3): trace tests to requirements.

## Code changes

### Patch (copy your changes or the add git command to show them) git diff ...

Optional (point 4): the patch is clean.

Optional (point 5): considered for acceptance (passes all automated checks).

## Test results Overall results with link to a copy or excerpt of the logs (before/after refactoring).

## UML class diagram and its description ### Key changes/classes affected

Optional (point 1): Architectural overview.

## Architectural Overview

### System Purpose.

**Sir Lancebot** is an open-source `Discord bot` developed and maintained by the Python Discord community. Its primary purpose is to serve a beginner-friendly project for developers who want to learn and contribute to open source. The bot  provides a variety of features for Discord servers (fun games, utilities, seasonal commands, event tools).

In practice, the system combines a bot core with multiple independent features modules (cogs), so new functionality can be added with minimal impact on existing commands.

Our `Mathdoku` implementation follows the same philosophy: board logic is separated from Discord interaction and from the board-file parsing, which keeps each concern testable and replaceable.

### System Architecture

### Component Diagram

![alt text]()

The system architecture is organized in layers around a modular bot core.
`Users` interact through Discord, and the `Discord API` sends events and commands to the `Sir Lancebot Core`, which is responsible for runtime setup and dispatching functionality to the corresponding extension. Each `extension (Cog)` is independent, so features can be added, removed or modified independently without modifying the core logic. Our `Mathdoku` game implementation is included inside the `fun` feature group, but there are other fun features groups as `utilites`, `holidays`, `events`.

### Mathdoku Architecture in the system.

The `Mathdoku` feature is implemented as a subsystem across three modules with clear separation of responsibilities.

#### 1. Game Logic (`mathdoku.py`)
This module contains the core game model:
- **Cell:** stores coordinates (row, column), block, player guess, and correct value.
- **Block:** stores block metadata (id, operation, number, assigned cells, color).
- **Grid:** stores board state and game rules (latin-square rules, full-board checks, check block constraints, evaluates win condition, hint cooldown handling...).

This module is independent from Discord commands, so game correctness can be verified independently from the bot's event handling.

#### 2. Board Parsing (`mathdoku_parser.py`)
This module reads `mathdoku_boards.txt`, extract board definitions, builds `Grid` objects, assign blocks and operations, and loads the correct solution values.

This module acts as the entry point for board data, transforming raw text into structured game objects ready to be used by the game logic.

#### 3. Discord Integration (`mathdoku_integration.py`)
This module connects the game to Discord and manages the full interaction flow with the player:
- Starts a game session.
- Wait for player input messages with a 10 minutes inactivity timeout.
- Handles guesses from user inputs.
- Handles emoji reactions for hints and block validation.

This module contains no game rules. It receives player input messages,
delegates to the game logic, and sends the result back to Discord.

Optional (point 2): relation to design pattern(s).

## Overall experience What are your main take-aways from this project? What did you learn? How did you grow as a team, using the Essence standard to evaluate yourself?

Optional (point 6): How would you put your work in context with best software engineering practice?

Optional (point 7): Is there something special you want to mention here?
