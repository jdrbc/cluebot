# Clue Sheet Bot

Be the best detective! Give clue sheet bot all of the facts in a yaml file, and it will give you the best possible resulting cluesheet.

    SUSPECTS:       joe  bil  sam  kat  lin
    green__________ [X]  [X]  [X]  [!]  [X]
    mustard________ [A]  [A]  [A]  [A]  [A]
    peacock________ [X]  [X]  [X]  [X]  [!]
    plum___________ [X]  [X]  [X]  [!]  [X]
    scarlet________ [X]  [!]  [X]  [X]  [X]
    white__________ [X]  [X]  [-]  [-]  [-]

    WEAPONS:        joe  bil  sam  kat  lin
    candlestick____ [X]  [X]  [ ]  [ ]  [ ]
    dagger_________ [X]  [X]  [X]  [X]  [!]
    leadpipe_______ [X]  [X]  [!]  [X]  [X]
    revolver_______ [A]  [A]  [A]  [A]  [A]
    rope___________ [X]  [!]  [X]  [X]  [X]
    wrench_________ [!]  [X]  [X]  [X]  [X]

    ROOMS:          joe  bil  sam  kat  lin
    ballroom_______ [!]  [X]  [X]  [X]  [X]
    billiard_______ [X]  [X]  [ ]  [ ]  [ ]
    conservatory___ [X]  [!]  [X]  [X]  [X]
    dining_________ [X]  [X]  [ ]  [ ]  [ ]
    hall___________ [A]  [A]  [A]  [A]  [A]
    kitchen________ [X]  [X]  [ ]  [ ]  [ ]
    library________ [!]  [X]  [X]  [X]  [X]
    lounge_________ [X]  [X]  [ ]  [ ]  [ ]
    study__________ [X]  [X]  [ ]  [ ]  [ ]
    ***SOLVED: mustard in the hall with the revolver***

The bot tracks who has what card based on suggestions and answers, and infers the solution when a whole section is known. The bot also does some non-obvious inferrences:

1. infer cards based on past responses to suggestions. E.g. player responds to A B C but not X B C then player has A
2. compare unknown card count to number of unknown cards for a player. E.g. if player only has 1 card remaining & it could only be 1 card.
3. infer players cards when the section solution is known
4. infer cards not in the solution based on past accusations

# Running

Update `game.yml` with player names & your cards.
The order of the players must match the answering order (left to right usually).

- install pipenv
- install pyenv
- install python3
- install dependencies: `pipenv install`
- run `pipenv run python src/clue.py game.yml`

Keep the 'events' list in game.yml updated as you play. The cluesheet will automatically update in the terminal.

# game.yml

See the printed cluesheet for the correct spelling of the cards. Some spellings are slightly different from the game e.g. 'billiard room' is just 'billiard'.

See game.yml for example game & more examples in the example folder.

- **setup**:
  - **cards**: [OPTIONAL] override game cards see 'examples' for example
  - **players**: players starting with dealer from left to right
    - **name**
    - **cards**: required for you
    - **card_count**: required for other players
- **events:** list of game events in following formats

  - **suggestion by other player:**

    q: [asking player name] [suspect weapon room]

    a: [answering player name]

    _e.g._

    _q: bob lounge green candlestick_

    _a: joe_

    _or..._

    _q: bob lounge green candlestick_

    _a: nobody_

  - **suggestion by you:**

    q: [your name] [suspect weapon room]

    a: [answer player name] [revealed card]

    _e.g._

    _q: bob lounge green candlestick_

    _a: joe green_

    _or..._

    _q: bob lounge green candlestick_

    _a: nobody_

  - **reveal (e.g. after dropped card or clue card):**

    r: [possessing player name] [revealed card]

    _e.g._

    _r: bob dagger_

    _r: nobody hall_

  - **(failed) accusation:**

    accuse: [accusing player name] [suspect weapon room]

In any suggestion or reveal if nobody answers use the name 'nobody' to indicate that nobody answered.

The order of the cards after the player's name does not matter.

# The cluesheet

The cluesheet indicates the known state of players' hands with these symbols:

- **[A]** - this is the solution to the section
- **[⁈]** - either the player has this card or it is the solution
- **[!]** - the player has this card
- **[X]** - the player does not have this card
- **[-]** - this is _not_ the solution to the section, but the possessing player is unknown
- **[ ]** - current state unknown
