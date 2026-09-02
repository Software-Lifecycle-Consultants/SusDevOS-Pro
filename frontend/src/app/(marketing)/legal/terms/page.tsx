import type { Metadata } from "next";
import { LegalPage } from "../LegalPage";

export const metadata: Metadata = {
  title: "Terms of Service — SusDevOS",
  description: "Terms governing your use of SusDevOS. Governed by the laws of England and Wales.",
  alternates: { canonical: "https://susdevos.com/legal/terms" },
};

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" lastUpdated="1 September 2026">

      <p>
        These Terms of Service (&ldquo;Terms&rdquo;) govern your access to and use of the SusDevOS platform
        and website, operated by SusDevOS Ltd, a company registered in England and Wales
        (&ldquo;SusDevOS&rdquo;, &ldquo;we&rdquo;, &ldquo;us&rdquo;). By creating an account or using the service, you agree
        to these Terms. If you do not agree, do not use the service.
      </p>

      <h2>1. The service</h2>

      <p>
        SusDevOS provides a software-as-a-service platform for GHG emissions calculation, inventory
        management, target tracking, and ecosystem/biodiversity reporting. We grant you a
        non-exclusive, non-transferable, revocable licence to access and use the platform during
        your subscription period, subject to these Terms.
      </p>

      <h2>2. Accounts</h2>

      <p>
        You must provide accurate information when creating an account. You are responsible for
        maintaining the confidentiality of your login credentials and for all activity that occurs
        under your account. Notify us immediately at{" "}
        <a href="mailto:security@susdevos.com">security@susdevos.com</a> if you suspect unauthorised
        access to your account.
      </p>

      <p>
        You may not share your login credentials with others. Multi-user access is provided through
        the platform&apos;s user management and role-based access features. Each individual user must have
        their own account.
      </p>

      <h2>3. Subscription and billing</h2>

      <p>
        Paid plans are billed monthly or annually in advance. Annual plans are discounted and
        non-refundable once the billing period has started (except where required by law). Monthly
        plans can be cancelled at any time and will not renew after the current period ends.
      </p>

      <p>
        We may change plan prices on 30 days&apos; written notice. Continued use of the service after
        a price change constitutes acceptance of the new pricing. You can cancel at any time to
        avoid future charges.
      </p>

      <p>
        Failure to pay will result in account suspension after a 7-day grace period, and account
        termination after 30 days. Your data is retained for 60 days after termination and can be
        exported during that period on request.
      </p>

      <h2>4. Free plan</h2>

      <p>
        The free plan is provided without charge and without any warranty. We reserve the right to
        modify, limit, or discontinue the free plan at any time on 30 days&apos; notice. Free plan
        accounts that have been inactive for 12 consecutive months may be deleted.
      </p>

      <h2>5. Founding 10 programme</h2>

      <p>
        The Founding 10 programme is available to up to ten organisations selected by SusDevOS.
        Submitting an application does not reserve or guarantee a place. A place is confirmed only
        after a fit review, execution of a Founding 10 programme agreement, and account activation.
      </p>

      <p>
        An activated participant receives a 100% Founding Partner Credit against the SusDevOS
        platform fee for 24 months from its activation date. The standard allowance is one
        organisation, up to ten named users, ten active projects, five reporting years, and 500 MB
        of file storage. The programme includes two 60-minute onboarding sessions, email support
        with a two-business-day response target, a monthly group clinic, and the exit assistance
        described below. Response targets are not a service-level agreement.
      </p>

      <p>
        Participants agree to nominate an internal champion, begin onboarding within 30 days,
        provide usable project or reporting data within 45 days, and participate in monthly
        feedback during the first three months followed by quarterly reviews. Permission to publish
        a participant&apos;s name, logo, quotation, or identifiable case study will always require
        separate written approval. SusDevOS may use anonymised and aggregated product feedback and
        usage insights that do not identify the participant or disclose its confidential data.
      </p>

      <p>
        The programme does not include custom software development, bespoke integrations, historical
        data cleansing, consultancy or assurance services, dedicated infrastructure, SSO, a formal
        uptime SLA, premium third-party datasets or commercial API licences. Any separately agreed
        work will be scoped and priced in writing before it begins.
      </p>

      <p>
        At the end of the 24-month term, a participant may move to a then-current hosted plan,
        export its data and close the account, or self-host SusDevOS for its own internal use under
        the applicable software licence. Exit assistance includes a structured export, the standard
        deployment guide, up to two hours of remote handover assistance, and responses to migration
        questions for 30 days. The participant is responsible for its own cloud infrastructure,
        operations, security, backups, third-party services, and any bespoke migration work.
      </p>

      <p>
        If a Founding 10 programme agreement conflicts with these general Terms, the programme
        agreement controls for that participant and programme term.
      </p>

      <h2>6. Acceptable use</h2>

      <p>You agree not to:</p>

      <ul>
        <li>Use the service for any unlawful purpose or in violation of any applicable laws or regulations</li>
        <li>Attempt to gain unauthorised access to the platform, other accounts, or our infrastructure</li>
        <li>Submit false, misleading, or fraudulent emissions data with intent to deceive auditors, regulators, or investors</li>
        <li>Reverse-engineer, decompile, or disassemble any part of the platform</li>
        <li>Use automated tools to scrape, copy, or mirror platform content without written permission</li>
        <li>Introduce malware, viruses, or any code designed to disrupt the platform</li>
        <li>Resell or sublicence access to the platform without written agreement</li>
      </ul>

      <h2>7. Your data</h2>

      <p>
        You own your emissions data, reports, and all content you enter into SusDevOS. We process
        it only to provide the service. You can export your data at any time in CSV or JSON format.
        On account termination, we will make your data available for export for 60 days.
      </p>

      <p>
        You grant us a limited licence to store, process, and display your data to provide the
        service. We do not sell your data to third parties. See our{" "}
        <a href="/legal/privacy">Privacy Policy</a> and{" "}
        <a href="/legal/dpa">Data Processing Agreement</a> for full details.
      </p>

      <h2>8. GHG calculations and accuracy</h2>

      <p>
        SusDevOS calculates GHG emissions using methodology derived from the GHG Protocol Corporate
        Standard, IPCC AR6, and authoritative emission factor datasets. Whilst we take care to
        ensure our calculations are accurate, we cannot guarantee that calculated emissions figures
        will be accepted by any specific verifier, regulator, or standard body.
      </p>

      <p>
        <strong>You are responsible</strong> for the accuracy and completeness of the activity data
        you input, your organisational boundary choices, the appropriateness of the emission factors
        you select, and the final emissions figures you disclose or report. SusDevOS is a calculation
        tool, not a substitute for professional sustainability advice.
      </p>

      <h2>9. Intellectual property</h2>

      <p>
        The SusDevOS platform, its software, design, and content are owned by SusDevOS Ltd and
        protected by copyright and other intellectual property laws. These Terms do not transfer
        any intellectual property rights to you. You may not copy, reproduce, or create derivative
        works from our platform without written permission.
      </p>

      <h2>10. Confidentiality</h2>

      <p>
        Each party agrees to keep the other party&apos;s confidential information confidential and not
        to use it for any purpose other than performing obligations under these Terms. Your emissions
        data is treated as confidential. Our product roadmap, pricing structures, and business terms
        are our confidential information.
      </p>

      <h2>11. Warranties and disclaimers</h2>

      <p>
        The service is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo;. To the maximum extent permitted by
        law, we disclaim all warranties, express or implied, including implied warranties of
        merchantability, fitness for a particular purpose, and non-infringement. We do not warrant
        that the service will be uninterrupted, error-free, or that calculated emissions figures
        will satisfy any specific regulatory or standard requirement.
      </p>

      <h2>12. Limitation of liability</h2>

      <p>
        To the maximum extent permitted by law, SusDevOS&apos;s total liability to you for any claim
        arising out of or related to these Terms or the service, regardless of the form of the
        action, is limited to the amounts you paid to SusDevOS in the 12 months preceding the claim.
      </p>

      <p>
        In no event will SusDevOS be liable for any indirect, incidental, special, consequential,
        or exemplary damages, including loss of profits, data, or business, even if advised of the
        possibility of such damages.
      </p>

      <p>
        Nothing in these Terms limits or excludes liability for death or personal injury caused by
        negligence, fraud or fraudulent misrepresentation, or any other liability that cannot be
        excluded by law.
      </p>

      <h2>13. Term and termination</h2>

      <p>
        These Terms begin when you create an account and continue until terminated. Either party
        may terminate at any time. We may suspend or terminate your account immediately if you
        breach these Terms, fail to pay, or engage in conduct that may harm other users or the
        platform.
      </p>

      <p>
        On termination, your right to use the service ends immediately. Sections 7 (Your data),
        9 (Intellectual property), 11 (Warranties), 12 (Limitation of liability), and 14
        (Governing law) survive termination.
      </p>

      <h2>14. Governing law</h2>

      <p>
        These Terms are governed by the laws of England and Wales. Any disputes arising from or
        in connection with these Terms shall be subject to the exclusive jurisdiction of the courts
        of England and Wales.
      </p>

      <h2>15. Changes to these Terms</h2>

      <p>
        We may update these Terms from time to time. We will provide at least 30 days&apos; notice
        of material changes by email. Continued use of the service after the effective date of
        the updated Terms constitutes acceptance.
      </p>

      <h2>16. Contact</h2>

      <p>
        For any questions about these Terms, contact us at{" "}
        <a href="mailto:hello@susdevos.com">hello@susdevos.com</a> or write to:
        SusDevOS Ltd, United Kingdom.
      </p>

    </LegalPage>
  );
}
