# GateRed -- Reddit Gateway API Library

TBD

### MISTAKE: should not based on single session

The correct way is to create a new session (client) when using new proxy connection.
To put it simple, proposed a class with general configs and raw functions.
Use enter/exit to open/close the httpx client.

Another class will then contain and perform the actual functions + pushshift. (submissions, sub_coms)

Also define Error class for better logging.

Set use reddit session header to true since client will be dispose after use
