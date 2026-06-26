import type { Metadata } from "next";
import { LegalPage } from "../LegalPage";

export const metadata: Metadata = {
  title: "Data Processing Agreement — SusDevOS",
  description:
    "SusDevOS Data Processing Agreement (DPA) under UK GDPR Article 28. Required for all customers whose use involves personal data.",
  alternates: { canonical: "https://susdevos.com/legal/dpa" },
};

export default function DPAPage() {
  return (
    <LegalPage title="Data Processing Agreement" lastUpdated="26 June 2026">

      <p>
        This Data Processing Agreement (&ldquo;DPA&rdquo;) forms part of the agreement between you
        (&ldquo;Controller&rdquo;) and SusDevOS Ltd (&ldquo;Processor&rdquo;) and applies where the use of the
        SusDevOS platform involves the processing of personal data on your behalf. It is required
        by Article 28 of UK GDPR and EU GDPR.
      </p>

      <p>
        By using SusDevOS on a paid plan, you accept this DPA. Enterprise customers requiring a
        countersigned copy should contact <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
      </p>

      <h2>1. Definitions</h2>

      <p>
        Terms not otherwise defined here have the meanings given in UK GDPR and EU GDPR.
        &ldquo;Personal Data&rdquo; means any information relating to an identified or identifiable natural
        person that you upload to or process via the SusDevOS platform. This includes — but is
        not limited to — named employee travel records, user account details of your staff, and
        any individually identifiable data in emissions records.
      </p>

      <p>
        Most emissions data (fuel consumption figures, energy use totals, activity quantities) is
        not personal data. This DPA applies only where personal data is involved.
      </p>

      <h2>2. Roles and responsibilities</h2>

      <p>
        You (&ldquo;Controller&rdquo;) determine the purposes and means of processing personal data that you
        upload to SusDevOS. SusDevOS (&ldquo;Processor&rdquo;) processes that data only on your documented
        instructions and only to provide the platform services described in the Terms of Service.
      </p>

      <p>
        SusDevOS is independently a Controller for user account data (login details, authentication
        logs, billing information). That processing is governed by the{" "}
        <a href="/legal/privacy">Privacy Policy</a>, not this DPA.
      </p>

      <h2>3. Subject matter and duration</h2>

      <p>
        The subject matter of processing under this DPA is the provision of the SusDevOS GHG
        reporting and ecosystem tracking platform. Processing begins when you start using the platform
        and continues until your account is terminated, after which personal data is retained or
        deleted per Section 8 below.
      </p>

      <h2>4. Nature and purpose of processing</h2>

      <p>
        We process personal data for the following purposes, and only to the extent necessary for
        each:
      </p>

      <ul>
        <li>Storing and calculating GHG emissions data that contains personal identifiers (e.g. named business travel)</li>
        <li>Maintaining audit log records of user actions for inventory integrity and regulatory compliance</li>
        <li>Sending platform notifications and alerts to named users</li>
        <li>Providing data export and GDPR data subject access request responses on your behalf</li>
      </ul>

      <h2>5. Types of personal data and data subjects</h2>

      <p>The personal data we may process on your behalf includes:</p>

      <table>
        <thead>
          <tr>
            <th>Data type</th>
            <th>Data subjects</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>User names and work email addresses</td>
            <td>Your employees, contractors, consultants</td>
          </tr>
          <tr>
            <td>Employee commuting journey data (Scope 3 Category 7)</td>
            <td>Your employees (if individually identifiable)</td>
          </tr>
          <tr>
            <td>Named business travel records</td>
            <td>Your employees or travellers</td>
          </tr>
          <tr>
            <td>Supplier contact data (if entered)</td>
            <td>Your suppliers&apos; named contacts</td>
          </tr>
          <tr>
            <td>Audit log entries containing user identity</td>
            <td>Your platform users</td>
          </tr>
        </tbody>
      </table>

      <h2>6. Obligations of the Processor (SusDevOS)</h2>

      <p>SusDevOS agrees to:</p>

      <ul>
        <li>Process personal data only on your documented instructions and not for any other purpose</li>
        <li>Ensure all persons with access to the personal data are bound by appropriate confidentiality obligations</li>
        <li>Implement appropriate technical and organisational security measures (see Section 7)</li>
        <li>Not engage a sub-processor without your prior consent (given by accepting this DPA for the sub-processors listed in Section 9)</li>
        <li>Notify you within 24 hours of becoming aware of a personal data breach involving your data</li>
        <li>Assist you in fulfilling your GDPR obligations: data subject rights, DPIAs, breach notifications to supervisory authorities</li>
        <li>Return or delete personal data at termination (see Section 8)</li>
        <li>Make available all information necessary to demonstrate compliance with this DPA and permit audits on reasonable notice</li>
      </ul>

      <h2>7. Security measures</h2>

      <p>
        SusDevOS implements and maintains the following technical and organisational measures to
        protect personal data:
      </p>

      <ul>
        <li><strong>Encryption at rest:</strong> AES-256 encryption for all database storage and file storage</li>
        <li><strong>Encryption in transit:</strong> TLS 1.3 (minimum TLS 1.2) for all data transmission</li>
        <li><strong>Access control:</strong> Role-based access control with least-privilege principle; SuperAdmin MFA required</li>
        <li><strong>Tenant isolation:</strong> Row-level data isolation — each entity&apos;s data is architecturally separated</li>
        <li><strong>Authentication:</strong> JWT with 15-minute expiry and server-side token revocation; Argon2id password hashing</li>
        <li><strong>Audit logging:</strong> Immutable logs of all access to personal data with user identity and timestamp</li>
        <li><strong>Monitoring:</strong> AWS GuardDuty, application error monitoring with PII scrubbing, 24/7 alerting</li>
        <li><strong>Patch management:</strong> Critical security patches applied within 14 days; automated dependency updates via Dependabot</li>
        <li><strong>Penetration testing:</strong> Annual third-party penetration test; findings remediated before production deployment</li>
        <li><strong>Certification:</strong> Cyber Essentials certified; ISO 27001 in progress</li>
      </ul>

      <h2>8. Return and deletion of data</h2>

      <p>
        On termination of your account or on your written request, SusDevOS will, at your election:
      </p>

      <ul>
        <li>Provide a complete export of your data in JSON or CSV format within 30 days; or</li>
        <li>Delete all personal data from live systems within 30 days, and from backup systems within 90 days</li>
      </ul>

      <p>
        SusDevOS may retain personal data that is required to be kept by applicable law (e.g. billing
        records for 7 years under UK financial regulations) or that is necessary to defend legal claims.
        Audit log entries for verified GHG inventories are retained per the retention tier of your plan
        even after deletion, as these records may be required for regulatory compliance.
      </p>

      <h2>9. Sub-processors</h2>

      <p>
        You consent to SusDevOS engaging the following sub-processors. SusDevOS will notify you
        30 days before adding any new sub-processor, giving you the right to object.
      </p>

      <table>
        <thead>
          <tr>
            <th>Sub-processor</th>
            <th>Purpose</th>
            <th>Location</th>
            <th>Transfer mechanism</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Amazon Web Services</td>
            <td>Cloud infrastructure, database, file storage</td>
            <td>UK/EU regions</td>
            <td>UK/EU adequacy</td>
          </tr>
          <tr>
            <td>Stripe</td>
            <td>Payment processing (billing data only)</td>
            <td>UK/EU</td>
            <td>UK/EU adequacy</td>
          </tr>
          <tr>
            <td>Sentry</td>
            <td>Error monitoring (PII scrubbed before upload)</td>
            <td>United States</td>
            <td>Standard Contractual Clauses (EU SCCs Module 2 + UK IDTA)</td>
          </tr>
        </tbody>
      </table>

      <h2>10. International transfers</h2>

      <p>
        Personal data is primarily processed within the UK and EU. Where transfers to third countries
        occur (e.g. Sentry in the US), SusDevOS relies on appropriate safeguards: EU Standard
        Contractual Clauses (Module 2: controller-to-processor) and, for UK personal data,
        the UK International Data Transfer Agreement (IDTA) approved by the ICO.
      </p>

      <h2>11. Audit rights</h2>

      <p>
        You may audit SusDevOS&apos;s compliance with this DPA on reasonable written notice of at least
        30 days and no more than once per year, at your cost. As an alternative, SusDevOS will
        provide its most recent third-party penetration test executive summary and Cyber Essentials
        certification on request under NDA. Enterprise customers may negotiate additional audit
        rights in a bespoke agreement.
      </p>

      <h2>12. Liability</h2>

      <p>
        Each party&apos;s liability under this DPA is subject to the limitations and exclusions set
        out in the <a href="/legal/terms">Terms of Service</a>. Nothing in this DPA limits either
        party&apos;s liability for losses that cannot be excluded under applicable data protection law.
      </p>

      <h2>13. Governing law</h2>

      <p>
        This DPA is governed by the laws of England and Wales and subject to the exclusive
        jurisdiction of the courts of England and Wales.
      </p>

      <h2>14. Contact</h2>

      <p>
        For questions about this DPA, to request a countersigned copy, or to exercise your rights
        as a controller, contact our Data Protection Officer at{" "}
        <a href="mailto:dpo@susdevos.com">dpo@susdevos.com</a>.
      </p>

    </LegalPage>
  );
}
