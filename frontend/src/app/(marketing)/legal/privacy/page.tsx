import type { Metadata } from "next";
import { LegalPage } from "../LegalPage";

export const metadata: Metadata = {
  title: "Privacy Policy — SusDevOS",
  description: "How SusDevOS collects, uses, and protects your personal data. UK GDPR compliant.",
  alternates: { canonical: "https://susdevos.com/legal/privacy" },
};

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" lastUpdated="26 June 2026">

      <p>
        SusDevOS Ltd (&ldquo;SusDevOS&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;) is committed to protecting your personal data.
        This policy explains what personal data we collect, why we collect it, how long we keep it,
        and what rights you have over it. It applies to susdevos.com and the SusDevOS application.
      </p>

      <p>
        SusDevOS Ltd is registered in England and Wales. We are registered with the Information
        Commissioner&apos;s Office (ICO) as a data controller and data processor.
        Our Data Protection Officer can be reached at{" "}
        <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
      </p>

      <h2>1. Data we collect and why</h2>

      <h3>Account and user data</h3>
      <p>
        When you create an account, we collect your name, work email address, and password (stored
        as an Argon2id hash — we never store your plaintext password). We use this data to provide
        the service you signed up for. The legal basis is <strong>contract</strong> (Article 6(1)(b) UK GDPR).
      </p>

      <h3>Usage and authentication data</h3>
      <p>
        We log authentication events (login, logout, token refresh) including IP address, user agent,
        and timestamp. We also maintain an immutable audit log of all actions taken within the
        platform. The legal basis is <strong>legitimate interest</strong> (Article 6(1)(f)) — security,
        fraud prevention, and the integrity of verified GHG inventories.
      </p>

      <h3>Emissions and sustainability data</h3>
      <p>
        The GHG emissions figures, activity data, land parcel geometry, and project data you enter
        are business operational data. This is not personal data in most cases. Where it does contain
        personal data (e.g. named employee travel records), you are the data controller and we are
        your data processor. See the <a href="/legal/dpa">Data Processing Agreement</a> for details.
      </p>

      <h3>Marketing and lead data</h3>
      <p>
        If you contact us, subscribe to our newsletter, or use the carbon estimator tool, we collect
        your email address and any information you provide. We use this to respond to enquiries and,
        where you have opted in, to send product updates. The legal basis is <strong>consent</strong>{" "}
        (Article 6(1)(a)) for newsletter subscriptions, and <strong>legitimate interest</strong>{" "}
        (Article 6(1)(f)) for follow-up to existing customer enquiries.
      </p>

      <h3>Payment data</h3>
      <p>
        Payment processing is handled by Stripe. We store only your Stripe customer ID and invoice
        references — we never see or store your card number. Stripe&apos;s privacy policy governs
        their handling of payment data.
      </p>

      <h2>2. Data retention</h2>

      <table>
        <thead>
          <tr>
            <th>Data type</th>
            <th>Retention period</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>User account (active)</td><td>Account lifetime</td></tr>
          <tr><td>User account (deleted/closed)</td><td>90 days, then anonymised</td></tr>
          <tr><td>Authentication logs</td><td>12 months</td></tr>
          <tr><td>Audit logs — Free/Starter plans</td><td>30 days</td></tr>
          <tr><td>Audit logs — Professional/Agency plans</td><td>1 year</td></tr>
          <tr><td>Audit logs — Enterprise plans</td><td>7 years</td></tr>
          <tr><td>GHG inventory and emissions data</td><td>Account lifetime; exported on request</td></tr>
          <tr><td>Marketing lead data</td><td>Until unsubscribe + 6 months</td></tr>
          <tr><td>Billing records</td><td>7 years (UK financial records requirement)</td></tr>
        </tbody>
      </table>

      <h2>3. Your rights under UK GDPR</h2>

      <p>You have the following rights regarding your personal data:</p>

      <ul>
        <li>
          <strong>Right of access</strong> — request a copy of all personal data we hold about you.
          Submit via <a href="/app/settings">Account Settings</a> or email <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
          We will respond within 30 days and provide a machine-readable export.
        </li>
        <li>
          <strong>Right to erasure</strong> — request deletion of your account and personal data.
          We anonymise rather than hard-delete (to preserve audit log integrity for verified inventories).
          Your name is replaced with [Deleted User] and your email with a hashed placeholder.
        </li>
        <li>
          <strong>Right to rectification</strong> — update your name, email, and other account details
          at any time via Account Settings.
        </li>
        <li>
          <strong>Right to data portability</strong> — receive your data in a structured, machine-readable
          format (JSON) via the data export endpoint.
        </li>
        <li>
          <strong>Right to object</strong> — opt out of marketing emails via the unsubscribe link in
          any email, or contact us at <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
        </li>
        <li>
          <strong>Right to restrict processing</strong> — in limited circumstances, request that we
          restrict how we process your data. Contact <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
        </li>
      </ul>

      <p>
        To exercise any of these rights, email <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
        We will respond within 30 days. You also have the right to lodge a complaint with the ICO
        at <a href="https://ico.org.uk" target="_blank" rel="noopener noreferrer">ico.org.uk</a> if you
        believe we have not handled your data correctly.
      </p>

      <h2>4. Sub-processors</h2>

      <p>
        We use the following third-party services that process personal data on our behalf:
      </p>

      <table>
        <thead>
          <tr>
            <th>Processor</th>
            <th>Purpose</th>
            <th>Location</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Amazon Web Services</td>
            <td>Cloud infrastructure, database, file storage</td>
            <td>UK/EU regions</td>
          </tr>
          <tr>
            <td>Stripe</td>
            <td>Payment processing</td>
            <td>UK/EU</td>
          </tr>
          <tr>
            <td>Sentry</td>
            <td>Error monitoring (PII scrubbed before transmission)</td>
            <td>US (SCCs in place)</td>
          </tr>
        </tbody>
      </table>

      <p>
        External data providers (DEFRA, Climatiq, GBIF, ECB, Companies House, Verra) receive only
        non-personal query data (activity types, species names, company registration numbers). They
        are not sub-processors for personal data.
      </p>

      <p>
        We will notify you 30 days before adding a new sub-processor. The current sub-processor
        list is also available at <a href="/security">susdevos.com/security</a>.
      </p>

      <h2>5. International transfers</h2>

      <p>
        Our primary infrastructure is hosted in AWS UK/EU regions. Where data is transferred outside
        the UK/EEA (e.g. Sentry in the US), we rely on Standard Contractual Clauses (SCCs) or the
        UK&apos;s International Data Transfer Agreement (IDTA) as the transfer mechanism.
      </p>

      <h2>6. Cookies</h2>

      <p>
        The SusDevOS application uses one HttpOnly session cookie for authentication (your refresh
        token). This cookie is strictly necessary for the service to function and does not require
        consent under PECR. We do not use advertising or tracking cookies. Analytics, if used,
        are privacy-preserving and do not transmit personal data to third parties.
      </p>

      <h2>7. California residents (CCPA)</h2>

      <p>
        We do not sell or share your personal information with third parties for their own marketing
        purposes. California residents have additional rights under CCPA/CPRA. Contact{" "}
        <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a> to exercise these rights.
      </p>

      <h2>8. Changes to this policy</h2>

      <p>
        We may update this policy from time to time. Material changes will be notified by email to
        registered users at least 14 days before they take effect. The latest version is always
        available at <a href="/legal/privacy">susdevos.com/legal/privacy</a>.
      </p>

      <h2>9. Contact</h2>

      <p>
        For any privacy-related enquiries, contact our Data Protection Officer at{" "}
        <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a> or write to:
      </p>

      <p>
        Data Protection Officer<br />
        SusDevOS Ltd<br />
        United Kingdom<br />
        <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>
      </p>

    </LegalPage>
  );
}
