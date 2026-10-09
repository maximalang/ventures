# Manage dots permissions and capabilities

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

A dot is a personal agent in ChatGPT with its own cloud computer. Members can [assign ongoing work](https://learn.chatgpt.com/docs/dots/getting-started#give-it-a-first-task), such as research or recurring updates, then review its progress and results.

Learn more in the [ChatGPT dots guide](https://learn.chatgpt.com/docs/dots).

Admins decide who can use dots and which computers, apps, and communication channels they can use. Review action and approval settings before enabling access.

For detailed setup and day-to-day use, see [Getting started with your dot](https://help.openai.com/en/articles/20001530) in the Help Center.







<span
  id="can-we-use-o-if-our-workspace-requires-ekm-or-zdr"
  data-localization-body-anchor
/>

<span
  id="does-background-work-count-toward-usage-limits"
  data-localization-body-anchor
/>




## Set up dots for work










### 1. Configure role-based access

Workspace owners manage access through workspace defaults and custom roles assigned to groups. Review these permissions in Permissions &amp; roles:

- **Use dots**: Allow members to use dots.

- **Add dots to Slack**: Allow members to add dots to Slack.

- **Allow local computer access**: Allow dots to use a member’s local computer.

- **Use custom rules for dots**: Allow members to add or edit rules for their dots.

For role creation, assignment, and access checks, see the [role-based access control guide](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions#set-the-workspace-default-then-create-targeted-custom-roles).

Before changing [cloud-computer controls](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions#review-work-local-and-work-cloud-permissions) or Use password manager, review how they apply across dots and Work Cloud.

1. Open **Workspace settings &gt; Permissions &amp; roles**.

2. Under Permissions &gt; Workspace default &gt; Workspace capabilities, enable Use dots (Beta) if it should be available by default; otherwise grant access through a custom role.

3. Set Slack participation and custom dot rules. Local computer access requires a separate admin opt-in; review [Work Cloud access controls](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-cloud-security#administrator-access-controls) before enabling it.

4. Under Cloud computer capabilities, enable Cloud browser use, Cloud network access, and Cloud computer use where your policies allow browsing websites, accessing online services, and interacting with apps. Review both workspace defaults and custom roles.

5. Under Workspace capabilities, set Use password manager according to your workspace policy.

6. Save, then check access for an intended member.

Granting permission does not connect a service or enable computer access. Members complete [Slack](https://learn.chatgpt.com/docs/dots/channels#slack) and [local-computer setup](https://learn.chatgpt.com/docs/dots/computers-and-apps#connect-your-computer); supported existing app connections may already be available.

<span
  id="3-configure-approved-apps-and-actions"
  data-localization-body-anchor
/>




### 2. Configure app access

Dots can use supported existing ChatGPT app connections. Set app access and action restrictions in [Plugin controls](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors).

<span
  id="4-choose-communication-channels-and-destinations"
  data-localization-body-anchor
/>




### 3. Configure communication channels

Allow Slack participation for intended members, then have members complete the relevant channel setup.

Communication with a dot is separate from connecting apps that read or send work content.

**Before members connect their dots to Slack**

- **ChatGPT workspace owner:** Enable Use dots and Add dots to Slack for the intended members through workspace defaults or custom roles.

- **Slack workspace owner or app manager:** Ensure the ChatGPT app is installed in Slack. Approve app requests if required by your workspace. See [Slack’s app approval guidance](https://slack.com/help/articles/360024269514-Manage-app-requests-for-your-workspace).

- **Each member:** Connect your dot to Slack from its profile. See [Message your dot in Slack](https://learn.chatgpt.com/docs/dots/channels#slack).

Enabling the ChatGPT permission does not install an app in Slack or connect a member’s dot.

<span
  id="5-record-approval-and-oversight-responsibilities"
  data-localization-body-anchor
/>










<span
  id="manage-ongoing-work-and-access-changes"
  data-localization-body-anchor
/>




## Available admin controls

| **Area**                            | **Admin capability**                                                                                                  |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Access to dots                      | Grant or revoke dots access through workspace permissions.                                                            |
| Cloud and connected local computers | Control Cloud browser use, Cloud network access, Cloud computer use, Use password manager, and local-computer access. |
| Messaging and participation         | Enable or disable Slack participation.                                                                                |
| Connected apps                      | Set available apps and allowed actions through [Plugin controls](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors).              |
| Custom dot rules                    | When disabled, members cannot add or edit custom rules, and saved rules do not apply.                                 |
| Models                              | Enterprise model controls and defaults do not apply to dots.                                                          |







## Dots FAQ




### Access and eligibility

<span
  id="does-access-to-o-grant-access-to-apps-and-websites"
  data-localization-body-anchor
/>




<ToggleSection title="Does access to dots grant access to apps and websites?">

No. Dots access does not grant access to apps or websites. App connections require authorization; website work uses the browser’s signed-in account.

</ToggleSection>

<span
  id="whose-account-does-o-use-for-connected-work"
  data-localization-body-anchor
/>




<ToggleSection title="Whose account does a dot use for connected work?">

Review the connected account’s permissions in the source service and the cloud browser’s sign-in separately. See [Managing app accounts](https://help.openai.com/en/articles/20001494-connecting-and-managing-app-accounts-in-chatgpt).

</ToggleSection>

<span
  id="can-o-use-a-local-computer-vpn-or-existing-sign-in"
  data-localization-body-anchor
/>




<ToggleSection title="Can a dot use a local computer, VPN, or existing sign-in?">

A dot’s cloud computer is separate from a member’s local computer. Local work requires a connected, online computer with ChatGPT open and access enabled. Local sign-in, VPN access, and device policies do not automatically extend to the cloud computer.

</ToggleSection>

<span
  id="can-we-use-o-with-policies-that-target-an-operating-system"
  data-localization-body-anchor
/>




<ToggleSection title="How do cloud policies affect local computer access?">

If any cloud policy has `enforce_residency` enabled, local computer access is unavailable for dots. Work Cloud remains available. See [Work Cloud access controls](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-cloud-security#administrator-access-controls) for the policy requirements.

</ToggleSection>




### Actions and ongoing work

<span
  id="can-o-keep-working-when-the-user-is-away"
  data-localization-body-anchor
/>




<ToggleSection title="Can a dot keep working when the user is away?">

Yes. Members can assign [ongoing responsibilities](https://learn.chatgpt.com/docs/dots/tasks-and-memory#assigned-work). Workspace permissions and approval rules still apply. Local work requires the computer to stay online with ChatGPT open and access enabled.

[Proactive research](https://learn.chatgpt.com/docs/dots/tasks-and-memory#proactive-research) uses restricted tools to read connected apps; it cannot send messages, change content, or control a browser or computer. Acting on findings requires separate user authorization and applicable permissions and approvals.

</ToggleSection>







<ToggleSection title="Who can message a dot or see its results?">

Only the owner can direct their dot through a Slack direct message or supported channel mention. Messages from other people do not start work.

A dot may use other participants’ messages as context when its owner brings it into a Slack thread. Anyone with conversation access can see its posts. Context carried across channels does not authorize sharing with a new audience; check recipients before posting work content.

Microsoft Teams access is limited to an invite-only alpha.

</ToggleSection>

<span
  id="does-o-always-ask-before-sending-or-changing-something"
  data-localization-body-anchor
/>




<ToggleSection title="Does a dot always ask before sending or changing something?">

[Auto-review](https://learn.chatgpt.com/docs/dots/controls#how-action-review-works) checks proposed actions against the user’s instructions, custom rules, and safety requirements. Drafting a message does not authorize sending it. Keep app authorization, allowed actions, and action approvals separate; see [app permissions](https://help.openai.com/en/articles/20001495-managing-app-permissions-in-chatgpt) for approval options.

</ToggleSection>

<span
  id="how-should-we-stop-work-or-remove-a-users-access"
  data-localization-body-anchor
/>




<ToggleSection title="How do admins revoke dots access?">

Revoke dots access through workspace permissions. Review app accounts and website sessions separately; removing dots access does not replace disconnecting an app or signing out of a website.

</ToggleSection>

<span
  id="how-do-custom-rules-affect-confirmations"
  data-localization-body-anchor
/>




<ToggleSection title="How do custom rules affect confirmations?">

Default rules govern when a dot can act, needs confirmation, or requires user action. They still apply when custom rules are off.

[Custom dot rules](https://learn.chatgpt.com/docs/dots/controls#set-custom-rules) guide actions and confirmations. When disabled, members cannot add or edit rules, and saved rules do not apply. Dots still follow default rules and explicit user instructions.

Custom rules cannot override built-in safety requirements. Turning them off does not require confirmation for every action; review capability and app approval settings.

</ToggleSection>

<span
  id="what-safeguards-help-protect-work-done-by-dots"
  data-localization-body-anchor
/>




<ToggleSection title="What safeguards help protect work done by dots?">

Built-in safeguards help defend against malicious instructions and can pause or stop work when monitoring detects a safety concern.

Members can review progress in [Activity View](https://learn.chatgpt.com/docs/dots/controls#review-work) and redirect work. Review consequential results before relying on them.

</ToggleSection>




### Models and usage

<span
  id="do-existing-model-controls-and-defaults-apply-to-o"
  data-localization-body-anchor
/>




<ToggleSection title="Do existing model controls and defaults apply to dots?">

No. Review dots access and capability permissions directly in workspace settings.

</ToggleSection>




<ToggleSection title="How should admins monitor adoption and usage?">

Review current usage terms before rollout. Use the [Analytics API](https://learn.chatgpt.com/docs/enterprise/analytics-api) for available adoption metrics.

</ToggleSection>

<span
  id="which-data-policies-should-we-review-for-o"
  data-localization-body-anchor
/>




### Data and compliance

OpenAI does not use ChatGPT Enterprise data to improve its models by default. For OpenAI’s business data commitments, see [Enterprise privacy](https://openai.com/enterprise-privacy/).

<span
  id="what-does-o-remember-between-requests"
  data-localization-body-anchor
/>




<ToggleSection title="What does a dot remember between requests?">

A dot can [create saved memories](https://learn.chatgpt.com/docs/dots/tasks-and-memory#persistent-memory), including information from connected apps. Disconnecting an app does not delete information already obtained. Review saved memories and [reset options](https://learn.chatgpt.com/docs/dots/controls#reset-your-dot) when handling sensitive data or offboarding.

For separate ChatGPT memory settings and deletion steps, see the [Memory FAQ](https://help.openai.com/en/articles/8590148-memory-in-chatgpt).

</ToggleSection>

<span
  id="how-can-admins-investigate-work-o-has-done"
  data-localization-body-anchor
/>




<ToggleSection title="How can admins investigate work a dot has done?">

Use supported [Compliance API](https://learn.chatgpt.com/docs/enterprise/compliance-api#confirm-the-administration-boundaries) records to investigate user messages and dots’ replies. Confirm record coverage before relying on it for an audit.

</ToggleSection>