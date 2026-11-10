"""Built-in sample pages used for demos and regression tests."""

CLEAN_LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Northwind Analytics - Reporting for small teams</title>
  <style>
    .hero { animation: fade 1s ease; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
    @media (prefers-reduced-motion: reduce) {
      .hero { animation: none; }
    }
  </style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <header>
    <h1>Northwind Analytics</h1>
    <nav aria-label="Primary">
      <ul>
        <li><a href="/product">Product</a></li>
        <li><a href="/pricing">Pricing</a></li>
        <li><a href="/docs">Docs</a></li>
      </ul>
    </nav>
  </header>
  <main id="main">
    <section aria-labelledby="intro-heading">
      <h2 id="intro-heading">Reporting that answers real questions</h2>
      <p>Connect a warehouse or a database and get a dashboard your team
      actually reads. No SQL required to start.</p>
      <img src="hero-dashboard.png" alt="A dashboard showing monthly revenue by customer segment">
      <p><a href="/start">Start a free trial</a></p>
    </section>
    <section aria-labelledby="features-heading">
      <h2 id="features-heading">What you get</h2>
      <h3>Shared definitions</h3>
      <p>One metric definition per number, so everyone reads the same chart
      the same way.</p>
      <h3>Scheduled digests</h3>
      <p>Weekly summaries land in your inbox before the Monday meeting.</p>
    </section>
    <table>
      <caption>Plan comparison</caption>
      <thead>
        <tr>
          <th scope="col">Plan</th>
          <th scope="col">Seats</th>
          <th scope="col">Price</th>
        </tr>
      </thead>
      <tbody>
        <tr><th scope="row">Solo</th><td>1</td><td>Free</td></tr>
        <tr><th scope="row">Team</th><td>10</td><td>49</td></tr>
      </tbody>
    </table>
  </main>
  <footer>
    <p>Northwind Analytics</p>
  </footer>
</body>
</html>
"""

SIGNUP_FORM = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Create your account</title>
</head>
<body>
  <div class="signup-wrapper">
    <h1>Create your account</h1>
    <form action="/signup" method="post">
      <input type="text" name="first" placeholder="First name">
      <input type="email" name="email" placeholder="Work email">
      <input type="text" name="company" placeholder="Company">
      <input type="password" name="password" placeholder="Password">
      <input type="radio" name="plan" value="monthly"> Monthly
      <input type="radio" name="plan" value="yearly"> Yearly
      <label for="referral">How did you hear about us?</label>
      <select id="referral" name="referral">
        <option value="">Choose one</option>
        <option value="search">Search engine</option>
        <option value="friend">A colleague</option>
      </select>
      <p class="error">That email address is already registered.</p>
      <button type="submit" class="btn btn-primary">
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
          <path d="M2 8h10M8 2v12"></path>
        </svg>
      </button>
    </form>
  </div>
</body>
</html>
"""

BROKEN_NAV = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no, maximum-scale=1">
  <title>Shop</title>
</head>
<body>
  <div class="header">
    <div class="logo" onclick="goHome()">
      <img src="logo.png">
    </div>
    <div class="menu">
      <div onclick="openCategory('shoes')">Shoes</div>
      <div onclick="openCategory('bags')">Bags</div>
      <a href="/cart" tabindex="3">Cart</a>
      <a href="/account" tabindex="1">Account</a>
    </div>
  </div>
  <div class="banner">
    <img src="promo-banner.jpg">
    <img src="IMG_2291.png" alt="IMG_2291.png">
  </div>
  <h2>Featured</h2>
  <h4>Everyday sneakers</h4>
  <div class="filters" tabindex="0">
    <span>Filter by size</span>
  </div>
  <img src="sneaker-detail.jpg" alt="image of a sneaker">
</body>
</html>
"""

MEDIA_PLAYER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Product tour</title>
  <style>
    .intro { animation: slide 2s infinite; }
    @keyframes slide { from { transform: translateX(0); } to { transform: translateX(40px); } }
  </style>
</head>
<body>
  <video width="640" autoplay controls>
    <source src="tour.mp4" type="video/mp4">
  </video>
  <iframe src="https://example.com/player"></iframe>
  <marquee>Free shipping this week</marquee>
  <audio controls src="intro-theme.mp3"></audio>
  <img src="product.png" alt="">
  <div style="transition: all 0.3s ease; animation: pulse 1s infinite;">
    <span>Limited time offer</span>
  </div>
</body>
</html>
"""

ARIA_MESS = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Account settings</title>
</head>
<body>
  <main>
    <h1>Account settings</h1>
    <section aria-labelledby="missing-label">
      <h2 id="missing-label">Profile</h2>
      <p>The panel below is labelled by an element that does not exist.</p>
    </section>
    <div aria-labelledby="panel-title" role="region">
      <p>Settings content</p>
    </div>
    <div role="buton" tabindex="0" onclick="save()">Save changes</div>
    <button aria-hidden="true" tabindex="0">
      <svg viewBox="0 0 16 16"><path d="M0 0h16v16H0z"></path></svg>
    </button>
    <input id="dup" type="text" aria-label="First">
    <input id="dup" type="text" aria-label="Second">
    <a href="/help" aria-describedby="help-text">Help</a>
    <span id="help-text">Our team answers within a day.</span>
    <div role="list">
      <span>Not a list item</span>
    </div>
    <ul>
      <p>Not a list item either</p>
    </ul>
    <table>
      <tr><td>Cell</td><td>Cell</td></tr>
    </table>
  </main>
</body>
</html>
"""

DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Operations dashboard</title>
</head>
<body>
  <header>
    <h1>Operations</h1>
  </header>
  <main>
    <div class="cards">
      <svg viewBox="0 0 100 40" width="300" height="120">
        <polyline points="0,35 20,30 40,32 60,18 80,12 100,8"></polyline>
      </svg>
      <div class="metric">
        <span class="value">1,284</span>
        <span class="label">Orders today</span>
      </div>
    </div>
    <div id="status">Last sync 4 minutes ago</div>
    <table>
      <tr><td>North</td><td>412</td></tr>
      <tr><td>South</td><td>377</td></tr>
    </table>
    <iframe src="https://example.com/embed/map"></iframe>
    <a href="#"><svg viewBox="0 0 16 16"><path d="M0 0h16v16H0z"></path></svg></a>
    <div role="button" onclick="open()"></div>
  </main>
</body>
</html>
"""

SAMPLES = [
    {
        "id": "clean_landing",
        "label": "Clean marketing page",
        "blurb": "A well structured landing page: lang, landmarks, skip link, "
                 "scoped table headers, reduced motion honoured. The control "
                 "case.",
        "profile": "marketing",
        "html": CLEAN_LANDING,
    },
    {
        "id": "signup_form",
        "label": "Signup form",
        "blurb": "Placeholder-only labels, an orphaned error message, a radio "
                 "group with no fieldset and an icon-only submit button.",
        "profile": "form_heavy",
        "html": SIGNUP_FORM,
    },
    {
        "id": "broken_nav",
        "label": "Broken store navigation",
        "blurb": "Clickable divs, positive tabindex, missing alt text, zoom "
                 "blocked in the viewport meta.",
        "profile": "ecommerce",
        "html": BROKEN_NAV,
    },
    {
        "id": "media_player",
        "label": "Product tour player",
        "blurb": "Autoplay video with no captions, untitled iframe, a "
                 "marquee, and no prefers-reduced-motion handling.",
        "profile": "marketing",
        "html": MEDIA_PLAYER,
    },
    {
        "id": "aria_mess",
        "label": "ARIA mistakes",
        "blurb": "ARIA references that point nowhere, an invalid role, a "
                 "focusable aria-hidden button, duplicate ids and broken list "
                 "markup.",
        "profile": "general",
        "html": ARIA_MESS,
    },
    {
        "id": "dashboard",
        "label": "Operations dashboard",
        "blurb": "An unlabelled chart, a table with no header cells, a status "
                 "message with no live region and an icon-only link.",
        "profile": "general",
        "html": DASHBOARD,
    },
]

SAMPLES_BY_ID = {sample["id"]: sample for sample in SAMPLES}


def get_sample(sample_id):
    return SAMPLES_BY_ID.get(sample_id)


def sample_list():
    return [
        {
            "id": sample["id"],
            "label": sample["label"],
            "blurb": sample["blurb"],
            "profile": sample["profile"],
        }
        for sample in SAMPLES
    ]
