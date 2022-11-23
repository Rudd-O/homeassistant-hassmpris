# Connect your Linux music and video players to Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This software is the Home Assistant integration that lets you control all popular media player applications on Linux (VLC, Chromium, Amarok) directly from your Home Assistant hub.

Play your songs / movies / TV shows; pause, stop, seek; skip back/forward, directly from the comfort of your own couch, bedroom, office, bathtub or mobile phone.  Automations can control media players as well — your own wishes are fully programmable (e.g. pause music when you leave home, or "Alexa, play with VLC").

## Setup

This setup process has two steps.

1. Set this integration up inside Home Assistant.
2. Set the agent up on the computer you plan to control from Home Assistant.

## Set the integration up

The following instructions assume you have HACS going and it works correctly with your Home Assistant.

* Add [this repository](https://github.com/Rudd-O/homeassistant-hassmpris) to your Home Assistant's HACS repositories.
  * Go to the HACS panel in your Home Assistant UI, then click on *Integrations* at the top bar, then on the overflow menu to the right, click *Custom repositories*.
  * Paste this repository's URL (linked above) in the Repository field, then select *integration* as the category.
  * Select *Add*.
* Now click on the *Explore & download repositories* button at the bottom right of the HACS screen, then search for *MPRIS*. Yyou'll see the repository listed in the search results.  Install it as per the standard HACS integration installation instructions.
* Remember to restart your Home Assistant service after installing this integration.

## Set the agent up

Now set the agent up in the computer you wish to control remotely.  Follow the [agent setup instructions here](https://pypi.org/project/hassmpris-agent/) under the heading *Setup*.

As you follow those instructions, you will eventually get to the section *Pair with Home Assistant*.  When you get there, go to your Home Assistant, navigate through *Settings* to *Devices & Services*, and see if your agent computer was discovered.  If you see an entry ready to set up, you can add the agent right away, paying attention to the agent setup instructions.  If it does not show up, however, you can always add the IP address of your agent computer manually by using the *Add integration* button and selecting the MPRIS integration.

## More information

Further documentation for this integration is available [here](https://github.com/Rudd-O/home-assistant.io/blob/4b9081cbdfc196575b4174cae09710d2fda1ffbb/source/_integrations/hassmpris.markdown) as well as in [the agent page](https://github.com/Rudd-O/hassmpris_agent#setup).
