from user_scanner.core.confidence import Confidence, build_anchors, score
from user_scanner.core.result import Result

def hit(site_name, username="johndoe", **extra):
    return Result.taken(extra=extra).update(site_name=site_name, username=username)


def anchors_from(*confirmed, emails=("johndoe@gmail.com",)):
    return build_anchors(
        confirmed=confirmed,
        emails=emails,
        urls=("https://github.com/johndoe", "https://stackoverflow.com/users/12345/johndoe"),
    )


CONFIRMED = hit(
    "Github",
    name="Johnathan Doe",
    website="https://johndoe.com",
    links="https://johndoe.com, https://twitter.com/johndoe2",
)


def test_anchors_take_names_domains_and_emails_from_confirmed_hits():
    anchors = anchors_from(CONFIRMED)

    assert "johnathandoe" in anchors.names
    assert "johndoe.com" in anchors.domains
    assert "johndoe@gmail.com" in anchors.emails


def test_anchors_ignore_platform_hosts():
    anchors = anchors_from(CONFIRMED)

    assert "twitter.com" not in anchors.domains
    assert "github.com" not in anchors.domains


def test_anchors_ignore_a_name_that_only_repeats_the_handle():
    anchors = anchors_from(hit("Github", name="JohnDoe"))

    assert "johndoe" not in anchors.names


def test_another_accounts_handle_does_not_suppress_a_real_name():
    anchors = anchors_from(
        hit("Linkedin", name="Johnathan Doe"),
        hit("Youtube", username="JohnathanDoe"),
    )

    assert "johnathandoe" in anchors.names


def test_a_named_site_is_confirmed():
    rating = score(hit("Github"), anchors_from(CONFIRMED), confirmed=True)

    assert rating is Confidence.CONFIRMED


def test_a_matching_name_is_likely():
    rating = score(hit("Behance", name="Johnathan Doe"), anchors_from(CONFIRMED))

    assert rating is Confidence.LIKELY


def test_a_personal_domain_in_the_bio_is_likely():
    rating = score(hit("Bluesky", bio="Dev - https://johndoe.com/"), anchors_from(CONFIRMED))

    assert rating is Confidence.LIKELY


def test_a_confirmed_profile_url_in_the_bio_is_likely():
    rating = score(
        hit("Instagram", bio="http://stackoverflow.com/users/12345/johndoe"),
        anchors_from(CONFIRMED),
    )

    assert rating is Confidence.LIKELY


def test_linking_a_confirmed_account_is_likely():
    anchors = anchors_from(hit("X (Twitter)", username="JohnDoe2"))
    twitch = hit("Twitch", twitter="https://twitter.com/JohnDoe2")

    assert score(twitch, anchors) is Confidence.LIKELY


def test_a_link_matches_a_confirmed_account_across_a_renamed_host():
    anchors = anchors_from(hit("X (Twitter)", username="JohnDoe2"))

    for url in ("https://x.com/johndoe2", "https://twitter.com/JohnDoe2/"):
        assert score(hit("Linktree", showcased_links=url), anchors) is Confidence.LIKELY


def test_a_link_to_an_unconfirmed_account_is_not_corroboration():
    anchors = anchors_from(hit("X (Twitter)", username="JohnDoe2"))
    other = hit("Linktree", showcased_links="https://x.com/somebodyelse")

    assert score(other, anchors) is Confidence.CANDIDATE


def test_the_scanned_email_in_the_bio_is_likely():
    rating = score(hit("Hackernews", bio="Reach me at johndoe@gmail.com"), anchors_from(CONFIRMED))

    assert rating is Confidence.LIKELY


def test_a_different_persons_name_conflicts():
    rating = score(hit("Chess.com", name="Other Person"), anchors_from(CONFIRMED))

    assert rating is Confidence.CONFLICTING


def test_a_descriptor_field_conflicts_on_its_name_part_only():
    rating = score(
        hit("Somesite", i_am="Other Person, 44, male"), anchors_from(CONFIRMED)
    )

    assert rating is Confidence.CONFLICTING


def test_a_descriptor_carrying_no_surname_does_not_conflict():
    rating = score(hit("Somesite", i_am="Someone, 44, male"), anchors_from(CONFIRMED))

    assert rating is Confidence.CANDIDATE


def test_a_name_that_only_renders_the_handle_stays_a_candidate():
    rating = score(hit("Picsart", name="john.d.oe"), anchors_from(CONFIRMED))

    assert rating is Confidence.CANDIDATE


def test_a_hit_with_no_metadata_stays_a_candidate():
    rating = score(hit("Roblox"), anchors_from(CONFIRMED))

    assert rating is Confidence.CANDIDATE


def test_nothing_conflicts_when_there_is_no_confirmed_account_to_conflict_with():
    rating = score(hit("Chess.com", name="Other Person"), anchors_from(emails=()))

    assert rating is Confidence.CANDIDATE
