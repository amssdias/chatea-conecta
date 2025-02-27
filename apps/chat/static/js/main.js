/**

TODO:

    - Create a way to erase all data in Redis: ?????
        - A command script from Django ?????
        - Make sure when erased, everyuser, even if they have their username on the localstorage, they should be logged out to connect again. ?????

    - When redeploying, Redis DB should be empty again

    - Build more pipelines:
        - prehooks for security of sensitive data
        - check security vulnerabilities (bandit)

    - Performance tests:
        - Locuster, Jmeter

    - Create maintenance page:
        - Create a model to check the environment and if its enabled
        - Create a html page saying its under maintenance
        - create middleware to check this new model and the environment, if enabled redirect.

    - Production steps:
        - Create instance
        - ENV variables
        - Collect static
        - Migrations
        - install daphne to run project on live (runserver only for development)
        - configure database separetly? or Docker is enough?

        - REDIS WORK ONLY ON DB -> 0 (Unless I use a VPS)

---------------------------------------------------------------------------------------
------------------------------- CURRENT -----------------------------------------------
---------------------------------------------------------------------------------------

    - Create file with messages, users and correct links for the usernames

    - Put it live
    - Create ADS
    - Make sure people adhere to the chat!
    - Create affiliate links
    - Create feature for private chats


    - Improve SEO <---------------

        - Analytics and Tracking
            - Integrate Google Analytics to track user behavior (e.g., session durations, click-through rates on bot messages).
            - Use Google Tag Manager to manage scripts without modifying Django templates.

        - SEO Testing: Use tools like Google Lighthouse or SEMrush to check keyword optimization.
            X - LighHouse
            - SEMruhse <---------------

    - Check how much space I will need for DB
    - Check how much space around I will need for Redis

    - Improve Design:
        - Make the chat container more appealing (better colors maybe)

    - Add LOGS:
        - Cloudwatch



    - Check how to bundle and pollify

    - FUTURE TODO
    - Make saying a small message saying (sendind and sent) on the chat
    - Create icon do not receive more messages from that group
    - Create a groupchat container for the favorites groups
    - Make the user know when there are messages from a group previously opened.
    - Chat with many rooms
    - Only adult rooms will be charged
    - If user violates rules of using some offensive words, he will get excluded from the group for a while.
    - Save the user on the localstorage so if he leaves the page and comes back, he dont need to rewrite a nickname
    - Create a button for user favourite groups:
        - This will store the favourite groups on the localstorage as well

    - Allow user to disconnect from groupchat:
        - On clicking on icon on top right or hovering the green button, let the user click and show modal to leave the group

---------------------------------------------------------------------------------------
---------------------------- HOST PLATFORMS -------------------------------------------
---------------------------------------------------------------------------------------

    - Build business:
        - Do not overload with promotional messages

        - Check websites to do marketing subscription on adult content:
            - Websites:
                - https://www.crakrevenue.com/
                    - Need to have my website deployed
                - jerkmate.com/affiliates (20$ per lead)
                    - It goes with crackrevenue
                - https://www.plugrush.com/
                - https://www.eroadvertising.com/ (banners and ads)
                - https://affiliateprograms.com/d/adult/
                - https://chaturbate.com/affiliates/
                    - Created account - To share the links, I choose each broadcaster and get the referall link
                    - I will need to change the task to if it's female, make sure the username gets her own message
                    - I can get payed by signup ($1.00), or by revShare, whatever the user spends, I get 20%
                    - I can use their own API to get the online rooms
                - https://bongacash.com/
                    - (Explanation on how to refer links (https://zorbasmedia.com/programs/bongacash-affiliate-program-review/)
                - https://stripcash.com/
                - https://affiliates.flirt4free.com/ (Looks legit)
                    - PPS and PPL
                    -
                - https://cpamatica.io/affiliates

            - check if I need to pay anything on this
            - Get the links and add them on my script

        - Put ads

    - Needs:
        - RAM: min 2GB - Low usage (beggining)
        - CPU: 2CPUs
        - Disk: 40GB

    - Where to HOST:
        - Hostinger VPS (DONT ACCEPT ADULT CONTENT)
            - VPS:
                - 4GB RAM + 1 CPU : 5€
                - 8GB RAM + 2 CPU: 5.99€
            - Cloud Hosting:
                - 3GB RAM + 2 CPU: 7.99€
                - 6GB RAM + 4 CPU: 13.00€

        - HostGator (Maybe?)
            - Web hosting: $2.75 Monthly
            - VPS $35 Monthly

        - KnownHost (Accepts):
            - Web hosting:
                - 1GB + 1CPU: $3.47
                - 2GB + 2CPU: $6.47
                - 4GB + 4CPU: $9.97
            - VPS (Unmanaged?):
                - 1GB + 1CPU: $5.00
                - 2GB + 1CPU: $10.00
                - 4GB + 2CPU: $20.00

        - MojoHost (Accept adult content?)
            - VPS:
                - 4GB RAM + 2CPU: $30

        - ViceTemplate (Accepts):
            - They offer to remake my website
            - They hosts for this purpose (adult)
            - Web hosting:
                - $6 (monthly)
            - VPS
                - 2RAM + 2CPU: $28 (monthly)
            - Sent them a msg to know if they can do me a frontend for my chat app

        - LunarVPS (Accepts):
            - VPS: $30 monthly

 */

import "./config.js";
import "./utils/create_elements.js";
import "./views/chatGroupsView.js";
import "./views/chatView.js";
import "./chatSocket.js";
import "./chatController.js";

