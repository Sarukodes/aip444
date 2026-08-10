import sys
from datetime import date, datetime
from urllib.parse import urlparse

import whois


def normalize_domain(value: str) -> str:
    value = value.strip()

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)

    domain = parsed.hostname or ""

    domain = domain.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None

    return value


def _serialize_date(value):
    value = _first(value)

    if isinstance(
        value,
        (datetime, date),
    ):
        return value.isoformat()

    if value is None:
        return None

    return str(value)


def whois_lookup(
    domain: str,
    verbose: bool = False,
) -> dict:

    clean_domain = normalize_domain(
        domain
    )

    if verbose:
        print(
            f'[DEBUG] Tool call: whois_lookup("{clean_domain}")',
            file=sys.stderr,
        )

    result = {
        "domain": clean_domain,
        "registrant_organization": None,
        "registration_date": None,
        "expiration_date": None,
        "registrar": None,
        "country": None,
        "error": None,
    }

    if not clean_domain:
        result["error"] = (
            "No valid domain supplied."
        )
        return result

    try:
        info = whois.whois(
            clean_domain
        )

        result[
            "registrant_organization"
        ] = _first(
            getattr(
                info,
                "org",
                None,
            )
        )

        result[
            "registration_date"
        ] = _serialize_date(
            getattr(
                info,
                "creation_date",
                None,
            )
        )

        result[
            "expiration_date"
        ] = _serialize_date(
            getattr(
                info,
                "expiration_date",
                None,
            )
        )

        result["registrar"] = _first(
            getattr(
                info,
                "registrar",
                None,
            )
        )

        result["country"] = _first(
            getattr(
                info,
                "country",
                None,
            )
        )

        if verbose:
            print(
                "[DEBUG] WHOIS: "
                f"registered={result['registration_date']}, "
                f"registrar={result['registrar']}, "
                f"country={result['country']}",
                file=sys.stderr,
            )

    except Exception as exc:
        result["error"] = str(exc)

        if verbose:
            print(
                f"[DEBUG] WHOIS lookup failed: {exc}",
                file=sys.stderr,
            )

    return result