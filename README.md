# watchful_eyes
Watchful Eyes is a Reddit Ban Bot

First of all I'm going to assume that if you're here, you already know how to install modules and run a bot. 

**Requirements**

- Enable Free form reports on your subreddit.  The bot uses free-form reports or it won't work.
- Fast Report userscript: https://github.com/paradox460/userscripts/tree/master/fast-report
- **While not technically required, it is highly recommended you install and use this userscript.  It makes custom reports much more simple.**

**Usage**

Once the script is running, the syntax is as follows:
- **Permanent bans are 0 days.**

ban  - # of days - ban reason char

Banning for 30 days for spam would read:  

> ban 30 s

Banning permanently for covid misinfo would read:

> ban 0 c


Table of ban reasons.

'c' : 'Covid Misinfo',

'v' : 'Violent Content',

'r' : 'Bigotry/Racism',

't' : 'Trolling',

's' : 'Spam',

'm' : 'Misinformation'

'b' : 'Brigading'

'h' : 'Hate Speech'

'd' : 'Dehumanizing Speech'


