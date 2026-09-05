# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Direct service connection keywords for RADKit Robot Framework library."""

from __future__ import annotations

import typing

from robot.api import logger
from robot.api.deco import keyword

from ..base import RADKitLibraryError
from ..utils import direct_service_id

if typing.TYPE_CHECKING:
    from typing import Any

    from robot.api.types import Secret


class DirectKeywords:
    """Keywords for RADKit direct service connections (without cloud)."""

    @keyword("RADKit Service Direct")
    def radkit_service_direct(
        self,
        username: str,
        password: Secret | str,
        host: str,
        port: int = 8181,
        sha256_fingerprint: str | None = None,
    ) -> Any:
        """<p>Connect to a RADKit service directly via host/port.</p>

            <p>The <code>password</code> must be provided either as a Robot
            <code>Secret</code> or as the name of an environment variable
            holding the value.</p>

            <p>The optional <code>sha256_fingerprint</code> can be used for
            remote host verification.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>username</code>: Username for the direct connection.</li>
                <li><code>password</code>: Password as Robot Secret or
                    env-var name.</li>
                <li><code>host</code>: Service host.</li>
                <li><code>port</code>: Service port (default 8181).</li>
                <li><code>sha256_fingerprint</code>: Optional SHA256 fingerprint
                    for host verification.</li>
            </ul>

            <p><strong>Returns:</strong> Connected RADKit service</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit Service Direct    superadmin    ENV_VAR_WITH_PASSWORD    remotehost
            </pre>
        """

        resolved_password = self._get_secret_or_env_only(password, "password")  # type: ignore[attr-defined]

        port = int(port)
        service_id = direct_service_id(host, port)

        existing = self.direct_services.get(service_id)  # type: ignore[attr-defined]
        if existing is not None:
            prior_user = self.direct_services_users.get(service_id)  # type: ignore[attr-defined]
            if prior_user != username:
                raise RADKitLibraryError(
                    f"Direct service session for {service_id} already exists "
                    f"with user '{prior_user}'. Disconnect the direct service "
                    "and reconnect with the new user."
                )
            logger.info(
                f"direct service {service_id} already connected as "
                f"{username}, no action performed"
            )
            self.current_service = existing  # type: ignore[attr-defined]
            return self.current_service  # type: ignore[attr-defined]

        args = {
            "username": username,
            "password": "<redacted>",
            "host": host,
            "port": port,
            "sha256_fingerprint": sha256_fingerprint,
        }
        logger.debug(
            "executing service_direct({})".format(
                ", ".join(f"{k}={v!r}" for k, v in args.items())
            )
        )

        service = self.client.service_direct(  # type: ignore[attr-defined]
            username=username,
            password=resolved_password,
            host=host,
            port=port,
            sha256_fingerprint=sha256_fingerprint,
        ).wait()
        if service is None:
            raise RADKitLibraryError("cannot connect to service directly")

        self.direct_services[service_id] = service  # type: ignore[attr-defined]
        self.direct_services_users[service_id] = username  # type: ignore[attr-defined]
        self.current_service = service  # type: ignore[attr-defined]
        logger.info(
            f"Selected service {getattr(self.current_service, 'name', service_id)}"  # type: ignore[attr-defined]
        )
        return self.current_service  # type: ignore[attr-defined]

    @keyword("RADKit Disconnect Direct Service")
    def radkit_disconnect_direct_service(
        self, host: str | None = None, port: int = 8181
    ) -> None:
        """<p>Disconnect from one or all direct RADKit service connections.</p>

            <p>If <code>host</code> is provided, disconnect only that specific
            direct service. If omitted, disconnect all direct services.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>host</code>: Optional host of the direct service to
                    disconnect.</li>
                <li><code>port</code>: Service port (default 8181).</li>
            </ul>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit Disconnect Direct Service    remotehost

        RADKit Disconnect Direct Service
            </pre>
        """

        port = int(port)
        if host:
            service_id = direct_service_id(host, port)
            service = self.direct_services.pop(service_id, None)  # type: ignore[attr-defined]
            self.direct_services_users.pop(service_id, None)  # type: ignore[attr-defined]
            if service is None:
                raise RADKitLibraryError(
                    f"No direct service connection to {service_id}"
                )
            service.logout()
            if self.current_service is service:  # type: ignore[attr-defined]
                self.current_service = None  # type: ignore[attr-defined]
            logger.info(f"Disconnected direct service {service_id}")
        else:
            if not self.direct_services:  # type: ignore[attr-defined]
                logger.info("No direct service connections to disconnect from")
                return
            if self.current_service is not None and self._is_direct_service(  # type: ignore[attr-defined]
                self.current_service  # type: ignore[attr-defined]
            ):
                self.current_service = None  # type: ignore[attr-defined]
            for sid, svc in self.direct_services.items():  # type: ignore[attr-defined]
                svc.logout()
                logger.debug(f"Disconnected direct service {sid}")
            self.direct_services.clear()  # type: ignore[attr-defined]
            self.direct_services_users.clear()  # type: ignore[attr-defined]
            logger.info("All direct service connections have been disconnected")
