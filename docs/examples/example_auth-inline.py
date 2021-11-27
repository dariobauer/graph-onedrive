from graph_onedrive import OneDrive


def main() -> None:
    """Print the usage of my OneDrive."""

    # Set config
    client_id = ""
    client_secret = ""
    tenant = "common"  # Optional, default set
    redirect_url = "http://localhost:8080"  # Optional, default set
    refresh_token = None  # Optional: from last session

    # Create session instance
    my_drive = OneDrive(client_id, client_secret, tenant, redirect_url, refresh_token)

    # Complete tasks using the instance. For this example we will just display the usage
    my_drive.get_usage(verbose=True)

    # OPTIONAL: Get refresh token that can be saved somewhere to recreate session
    # Suggested you use a configuration file and the context manager
    refresh_token = my_drive.refresh_token


if __name__ == "__main__":
    main()
