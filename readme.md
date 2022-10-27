Designed for use with Heroku Scheduler

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

I primarily made this to work with the [Discord job page.](https://boards.greenhouse.io/discord/) In theory, it should work on other basic Greenhouse job pages, like at https://boards.greenhouse.io/figma/.

On first run, it makes a database table and adds all of the current jobs. Then, in subsequecent runs, it looks at all the jobs on the page and checks if there is a difference from the database copy. If there is, it sends a Discord webhook notification about the new job. It then clears out the entire table and adds the current jobs anew. This is required because Heroku instances don't have any memory or filesystem that persist between runs, so the postgres database is used as it's form of memory.

It scrapes the jobs from the actual HTML of the page, not using any APIs. Thus, this repo can be prone to breakage if there's any major HTML changes.