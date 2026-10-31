# DevOps and infrastructure — technical interview

Ask only what changes the build. Each question carries a recommendation and a free-tier default; the user answers yes or names a change.

## Q1. Where does it run?

- **Recommend:** The simplest managed host that fits (a platform-as-a-service or a single container host) on a free tier; move up the ladder only on a measured trigger.
- **Free default:** Free tier of a managed host and a managed database.

## Q2. Which environments?

- **Recommend:** Local, a preview per pull request, and production. Add staging when paying users exist.
- **Free default:** Previews are free on most hosts.

## Q3. How is infrastructure defined?

- **Recommend:** Documented manual steps for the MVP if there is one environment; Terraform or similar once there are two or more environments to keep identical.
- **Free default:** No IaC until the second environment.

## Q4. Where do secrets live?

- **Recommend:** The host's secret store or a secret manager; never the repository; a secret scan runs in CI.
- **Free default:** None needed.

## Q5. How is a bad release undone?

- **Recommend:** One command or one click to the previous version, practised once before launch.
- **Free default:** None needed.

## Q6. What is the cost ceiling and who is told when it is hit?

- **Recommend:** A budget alert at 50, 80 and 100 percent to a named person.
- **Free default:** None needed.

