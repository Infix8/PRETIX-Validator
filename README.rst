Pretix Roll Number Validator
==========================

This is a plugin for `pretix`_ that ensures Roll Numbers entered during ticket purchase are unique within an event.

Installation
-----------

1. Download the plugin from the repository
2. Install the plugin files: ``pip install path/to/pretix-rollno-validator``
3. Enable the plugin in pretix's plugin settings
4. In your event settings, go to "Roll Number Settings" and select which question should be validated for uniqueness

Usage
-----

1. Create a question in your event that will collect Roll Numbers
2. Go to the plugin settings and select this question as the Roll Number field
3. When attendees try to purchase tickets, the plugin will ensure that:
   - No two orders can use the same Roll Number
   - Validation happens both during cart addition and order placement
   - If a Roll Number is taken between cart creation and order placement, the order will be cancelled

Development setup
---------------

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository.

3. Activate the virtual environment you use for pretix development.

4. Execute ``pip install -e .`` within this directory to register this application with pretix's plugin registry.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.

License
-------

Copyright 2024 Your Name

Released under the terms of the Apache License 2.0


.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html 