# Home Assistant MPRIS integration for Linux desktop media players

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This integration allows you to control your media player applications (VLC, Chromium, Amarok) from Home Assistant.  Play your media, pause, stop, seek, and skip back/forward, directly from the comfort of your own couch, bedroom or mobile phone.  Media players can be governed by automations as well, so you can program your own actions (e.g. pause music when you leave home, or "Alexa, play with VLC").

## Setup

First, setup the integration.  The following instructions assume you have HACS going and it works correctly with your Home Assistant.

* Add this (`homeassistant-hassmpris`) repository to your Home Assistant's HACS repositories.
  * Go to HACS, then click on *Integrations* at the top bar, then on the overflow menu to the right, click *Custom repositories*.
  * Paste this repository's URL in the Repository field, then select *integration* as the category.
  * Select *Add*.
* Now you'll see the repository listed under the *Integrations* heading.  Install it as per the standard HACS integration installation instructions.
* Remember to restart your Home Assistant instance.

Now, setup the agent in the computer you wish to control remotely.  Follow the [agent setup instructions here](https://pypi.org/project/hassmpris-agent/) under the heading *Setup*.

As you follow those instructions, you will eventually get to the section *Pair with Home Assistant*.  When you get there, go to your Home Assistant, navigate through *Settings* to *Devices & Services*, and add the MPRIS integration.  It is highly likely that you will see the MPRIS integration listed there, but if it isn't, you can always add the IP address of your computer manually by using the *Add integration* button and selecting the MPRIS integration.

From then on, you can pair your media computer with Home Assistant as per the instructions under *Pair with Home Assistant*.

## More information

Further documentation for this integration is available [here](https://github.com/Rudd-O/home-assistant.io/blob/4b9081cbdfc196575b4174cae09710d2fda1ffbb/source/_integrations/hassmpris.markdown) as well as in [the agent page](https://github.com/Rudd-O/hassmpris_agent#setup).
