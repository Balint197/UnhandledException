# Üdvözlünk az Unhandled Exception személyes pénzügyi asszisztensénél! 🚀🤖

Nyugodtan kezdj el chatelni a bottal a másik fülön. Az adataid felmérése után bővebb információhoz juthatsz pénzügyi helyzetedet illetően, valamint lépéseket tehetsz annak javításáért.

### TODO

* Make investment module - really simple
* OTP Persely mock + forgatókönyvek
* Make bot more friendly to be in line with initial requirements defined in the slides (https://docs.google.com/presentation/d/18o7qqmzCh2r2BhN_Awf6-wtOFh_VSVIwQfU6q5rQ_0c/)
  * ask for name, etc. in initial prompt, be more friendly
* buttons instead of natural typed function calls - check if data is ready before adding buttons  - check cookbook https://github.com/Chainlit/cookbook/
* Deploy on AWS or Vercel using docker

### Done

* Speech2Text (check streamlit config)
* Change prompt to include more data - probably something like long, short term goals, income, regular payments, emergency

  * in: income, investments
  * out: loans, rent, utilities, groceries, transportation, entertainment
  * goals:
    * anything, for demo let's go with a vacation as a short term goal
    * ask for a deadline
    * priority levels
    * can also have emergency budget, car, house, etc.
* Change `calculate_budget` with this new data in mind.
* Adatbevitel fv. - document upload? (check streamlit config)
