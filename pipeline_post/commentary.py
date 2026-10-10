"""Race commentary generator, ported from the demo page's JavaScript.

Builds become racehorses, authors become riders, results become WON/FELL.
The random choices use a seeded linear congruential generator that matches
the demo exactly, so the same builds always produce the same page:

    seed = (seed * 1103515245 + 12345) % 2147483648

A build dict carries: n, branch, author, status ("SUCCESS" or "FAILED"),
secs, failed_step (None or "install"/"test"/"deploy").
"""

DEFAULT_SEED = 20261009


class SeededRng:
    """Tiny seeded RNG. Call order determines output, so callers must keep
    the demo's order: race calls first, stewards' inquiries after."""

    def __init__(self, seed=DEFAULT_SEED):
        self.seed = seed

    def rnd(self):
        self.seed = (self.seed * 1103515245 + 12345) % 2147483648
        return self.seed / 2147483648

    def pick(self, options):
        return options[int(self.rnd() * len(options))]


def horse_name(branch):
    if branch == "main":
        return "Main Event"
    tail = branch.split("/")[-1].replace("-", " ")
    return " ".join(word.capitalize() for word in tail.split())


def fmt_time(secs):
    return "%dm %02ds" % (secs // 60, secs % 60)


def form_for(branch, builds):
    """Form figures for a branch, most recent first: 1 for a win, 0 for a fall."""
    return "-".join("1" if b["status"] == "SUCCESS" else "0"
                    for b in builds if b["branch"] == branch) or "debut"


def pace_word(secs, ok, rng):
    if not ok:
        return rng.pick(["a troubled trip", "a luckless run", "no luck in running"])
    if secs < 240:
        return rng.pick(["a blistering pace", "a scorching gallop", "gate-to-wire brilliance"])
    if secs < 360:
        return rng.pick(["a workmanlike run", "a professional performance", "a tidy effort"])
    return rng.pick(["a grinding staying performance", "a marathon effort", "a real test of stamina"])


def fail_word(step, rng):
    words = {
        "install": ["stumbled at the install hurdle",
                    "fell at the very first fence",
                    "never got out of the gate"],
        "test": ["came down at the test hurdle",
                 "was brought down in the testing stretch",
                 "faltered when the tests bit"],
        "deploy": ["was pulled up before the line",
                   "faded in the shadow of the post",
                   "found nothing when asked at deploy"],
    }
    return rng.pick(words.get(step, ["ran into trouble"]))


def race_call(build, rng):
    horse = horse_name(build["branch"])
    ok = build["status"] == "SUCCESS"
    t = fmt_time(build["secs"])
    if ok:
        return (
            "%s, ridden by %s, broke cleanly from gate #%s and set %s, "
            "stopping the clock at %s. %s"
            % (horse, build["author"], build["n"],
               pace_word(build["secs"], True, rng), t,
               rng.pick([
                   "The crowd in the merge queue loved it.",
                   "Connections will be eyeing the nightly handicap next.",
                   "A run that flatters the whole stable.",
                   "Never looked in danger after halfway.",
               ]))
        )
    step = build["failed_step"]
    return (
        "%s, under %s, %s and was recorded as a non-finisher after %s. %s"
        % (horse, build["author"], fail_word(step, rng), t,
           rng.pick([
               "The stewards will want a word about that %s step." % step,
               "Back to the training gallops for this one.",
               "Connections looked shell-shocked in the unsaddling enclosure.",
               "Money burned; the form book gets another blot.",
           ]))
    )


def inquiry(build, rng):
    return (
        "Build #%s (%s): %s after %s. %s"
        % (build["n"], horse_name(build["branch"]),
           fail_word(build["failed_step"], rng), fmt_time(build["secs"]),
           rng.pick([
               "The inquiry found no interference; the step simply beat it.",
               "Rider %s reported the mount was never travelling." % build["author"],
               "Connections have 48 hours to lodge an appeal, or just fix the step.",
               "No foul play suspected. Sometimes the pipeline just says no.",
           ]))
    )


def track_line(builds):
    fails = sum(1 for b in builds if b["status"] != "SUCCESS")
    going = "Heavy" if fails > 2 else ("Good to Soft" if fails > 0 else "Fast")
    return ("Track: %s - %d runners declared, %d non-finishers"
            % (going, len(builds), fails))


def headline(builds):
    latest = builds[0]
    horse = horse_name(latest["branch"]).upper()
    if latest["status"] == "SUCCESS":
        return "%s ROMPS HOME IN THE NIGHTLY HANDICAP" % horse
    return "DRAMA AT THE TURF AS %s FALLS" % horse
