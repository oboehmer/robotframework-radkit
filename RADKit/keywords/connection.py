# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Connection-related keywords for RADKit Robot Framework library."""

from __future__ import annotations

import base64
import os
import typing

import radkit_client
import radkit_client.version
from robot.api import logger
from robot.api.deco import keyword

from RADKit.base import RADKitLibraryError

try:
    from robot.api.types import Secret
except ImportError:
    Secret = None

if typing.TYPE_CHECKING:
    from typing import Any


class ConnectionKeywords:
    """Keywords for RADKit authentication, connection management, and timeout."""

    @keyword("RADKit Client Version")
    def radkit_client_version(self) -> str:
        """<p>Return the RADKit client library version installed.</p>

            <p><strong>Returns:</strong> radkit_client version string</p>

            <p><strong>Example:</strong></p>
            <pre>
        ${version}=    RADKit Client Version
            </pre>
        """
        version: str = radkit_client.version.version_str
        logger.info(f"radkit_client version {version}")
        return version

    @keyword("RADKit certificate login")
    def radkit_certificate_login(
        self,
        identity: str | None = None,
        cert_path: str | None = None,
        ca_path: str | None = None,
        key_path: str | None = None,
        private_key_password: str | Secret | None = None,
        domain: str | None = None,
    ) -> Any:
        """<p>Authenticate to RADKit cloud and create a RADKit client session.</p>

            <p>You can authenticate with multiple identities within the same test suite
            by executing this keyword multiple times with different identities &amp;
            certificates.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>identity</code>: Client identity (typically your Cisco Email
                    address), defaults to env var RADKIT_IDENTITY</li>
                <li><code>cert_path</code>: Path to RADKit certificate, defaults to env
                    var RADKIT_CERT_PATH or standard RADKit certificate location</li>
                <li><code>ca_path</code>: Path to RADKit CA certificate chain, defaults
                    to env var RADKIT_CA_PATH or standard RADKit certificate location</li>
                <li><code>key_path</code>: Path to RADKit certificate private key,
                    defaults to env var RADKIT_KEY_PATH or standard location</li>
                <li><code>private_key_password</code>: Passphrase for your private key.
                    Can be provided as a Robot Framework <code>Secret</code>
                    variable, or as the <em>name</em> of an environment variable
                    containing the password. When not provided, falls back to
                    env var RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64 (base64)
                    or RADKIT_CLIENT_PRIVATE_KEY_PASSWORD (cleartext).</li>
                <li><code>domain</code>: RADKit domain (defaults to PROD)</li>
            </ul>

            <p><strong>Returns:</strong> RADKit client object</p>

            <p><strong>Examples:</strong></p>
            <pre>
        # All arguments can also be provided via environment variables
        # (RADKIT_IDENTITY, RADKIT_CERT_PATH, RADKIT_KEY_PATH, etc.)
        RADKit certificate login    identity=user@cisco.com

        # Private key password from a named environment variable
        RADKit certificate login    identity=user@cisco.com
        ...    private_key_password=MY_PK_PASSWORD_ENV_VAR

        # Private key password using Robot Framework Secret variable
        # (define in *** Variables *** section)
        # ${PK_PASSWORD: Secret}    %{MY_PK_PASSWORD_ENV_VAR}
        RADKit certificate login    identity=user@cisco.com
        ...    private_key_password=${PK_PASSWORD}
            </pre>
        """
        identity = identity or os.environ.get("RADKIT_IDENTITY")
        domain = domain or "PROD"

        # Check if already connected with same identity/domain
        try:
            self._find_radkit_connection(  # type: ignore[attr-defined]
                identity, domain, radkit_client.AuthFlowType.CERTIFICATE
            )
        except ValueError:
            pass
        else:
            logger.info("RADKit client is already connected")
            return self.client  # type: ignore[attr-defined]

        resolved_password = self._get_private_key_password(private_key_password)
        if resolved_password is None:
            raise RADKitLibraryError(
                "Could not find private key password, neither passed as parameter, "
                "nor in environment as RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64 "
                "or RADKIT_CLIENT_PRIVATE_KEY_PASSWORD"
            )

        args: dict[str, Any] = {
            "identity": identity,
            "cert_path": cert_path or os.environ.get("RADKIT_CERT_PATH"),
            "key_path": key_path or os.environ.get("RADKIT_KEY_PATH"),
            "ca_path": ca_path or os.environ.get("RADKIT_CA_PATH"),
            "private_key_password": "<redacted>",  # mask for logging
            "domain": domain,
        }
        logger.debug(
            "executing certificate_login({})".format(
                ", ".join(f"{k}={v!r}" for k, v in args.items())
            )
        )
        args["private_key_password"] = resolved_password

        self.client.certificate_login(**args)  # type: ignore[attr-defined]
        logger.info(f"RADKit client is connected with identity {identity}")

        self.current_identity = identity  # type: ignore[attr-defined]
        logger.debug(
            f"Setting current identity to {identity} for subsequent "
            "RADKit select service calls"
        )

        logger.debug(
            f"cloud_connections:\n{self.client.cloud_connections}"  # type: ignore[attr-defined]
        )
        return self.client  # type: ignore[attr-defined]

    @staticmethod
    def _get_private_key_password(
        passwd: str | Secret | None,
    ) -> str | None:
        """Resolve private key password from argument or environment."""
        if passwd is not None:
            # Check for Robot Framework Secret type
            if Secret is not None and isinstance(passwd, Secret):
                return str(passwd.value)

            if isinstance(passwd, str):
                if passwd in os.environ:
                    return os.environ[passwd]
                raise RADKitLibraryError(
                    "private_key_password was passed as a plain string but does "
                    "not match any environment variable name. Pass the name of "
                    "an environment variable containing the password, or use "
                    "Robot Framework's Secret type. Passing literal password "
                    "values is not supported for security reasons."
                )

        b64_passwd = os.environ.get("RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64")
        if b64_passwd:
            return base64.b64decode(b64_passwd).decode()
        else:
            return os.environ.get("RADKIT_CLIENT_PRIVATE_KEY_PASSWORD")

    @keyword("RADKit disconnect")
    def radkit_disconnect(self, identity: str | None = None) -> None:
        """<p>Disconnect from all or selected RADKit cloud connections.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>identity</code>: Optional identity of the connection to
                    terminate. If not provided, all connections are disconnected.</li>
            </ul>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit disconnect

        RADKit disconnect    cxta-user@cisco.com
            </pre>
        """

        def _disconnect(conn: Any) -> None:
            logger.debug(f"disconnecting from connection {repr(conn)}")
            conn.logout()

        if identity:
            conn = self._find_radkit_connection(identity)  # type: ignore[attr-defined]
            _disconnect(conn)
        elif len(self.client.cloud_connections) > 0:  # type: ignore[attr-defined]
            conns = list(
                self.client.cloud_connections.values()  # type: ignore[attr-defined]
            )
            for conn in conns:
                _disconnect(conn)
            logger.info("All cloud connections have been disconnected")
        else:
            logger.info("No cloud connections to disconnect from")

        if len(self.client.cloud_connections) > 0:  # type: ignore[attr-defined]
            if identity and identity == self.current_identity:  # type: ignore[attr-defined]
                self.current_identity = list(  # type: ignore[attr-defined]
                    self.client.cloud_connections.values()  # type: ignore[attr-defined]
                )[-1].client_id
                logger.debug(
                    f"Setting current identity to "
                    f"{self.current_identity} for subsequent "
                    "RADKit select service calls"
                )
        else:
            self.current_service = None
            self.current_identity = None

    @keyword("RADKit select service")
    def radkit_select_service(self, serial: str, identity: str | None = None) -> Any:
        """<p>Connect to and select a remote RADKit service using its serial
            number/service-id.</p>

            <p>You can connect to more than one remote RADKit service during a test
            suite. Use this keyword to switch between remote services.</p>

            <p>The service you have last selected is used for all subsequent RADKit
            inventory or execute commands.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>serial</code>: Serial number of the remote RADKit service
                    instance.</li>
                <li><code>identity</code>: Optional RADKit identity (email address)
                    to use when multiple identities are active.</li>
            </ul>

            <p><strong>Returns:</strong> RADKit client service instance</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit select service    abcd-1234-efgh
        ${inventory}=    RADKit device inventory
            </pre>
        """
        identity = identity or self.current_identity
        try:
            service = self._find_service(serial, identity)  # type: ignore[attr-defined]
            logger.debug(f"service {serial} already connected, no action performed")
            self.current_service = service
        except KeyError:
            if serial in self.direct_services:  # type: ignore[attr-defined]
                self.current_service = self.direct_services[serial]  # type: ignore[attr-defined]
            else:
                connection = self._find_radkit_connection(identity)  # type: ignore[attr-defined]
                logger.info(
                    f"connecting to service {serial} with identity "
                    f"{connection.client_id}"
                )
                service = self.client.service(  # type: ignore[attr-defined]
                    serial, connection=connection
                ).wait(timeout=self.radkit_timeout)  # type: ignore[has-type]
                if service is None:
                    raise RADKitLibraryError("cannot connect to service") from None
                self.current_service = service
        logger.info(
            f"Selected service {getattr(self.current_service, 'serial', serial)}"  # type: ignore[attr-defined]
        )
        return self.current_service

    @keyword("RADKit timeout")
    def set_radkit_timeout(self, seconds: int | str) -> int:
        """<p>Set the time (in seconds) keywords will wait for a response from the
            RADKit service. Default is 300 seconds (5 minutes).</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>seconds</code>: Timeout in seconds.</li>
            </ul>

            <p><strong>Returns:</strong> Previous timeout value</p>

            <p><strong>Example:</strong></p>
            <pre>
        ${old_timeout}=    RADKit timeout    60
            </pre>
        """
        old_timeout: int = self.radkit_timeout  # type: ignore[has-type]
        self.radkit_timeout = int(seconds)  # type: ignore[attr-defined]
        return old_timeout
