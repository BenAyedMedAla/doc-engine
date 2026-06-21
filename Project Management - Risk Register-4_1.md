---
source: Project Management - Risk Register-4_1.xlsx
parser: kreuzberg
pages: 4
languages: eng, fra
---

## Cover

| Prepared By | Head of Infosec |
| --- | --- |
| Last updated date | 27.02.2025 |
| Approved By  | CPO |
| Last approval date | 27.02.2025 |

## PM Risk Register

|  |  |  |  |  |  |  |  |  |  | Risk Treatment Plan |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ID | Project / Feature | Risks | Past incidents linked to the risk | Risk Owner | Identification Date (start date of the new feature going through Change and Release Management) | Type | Severity | Status | Implemented security controls | Security controls part of risk treatment plans (where applicable) | Control implementation status | Residual Risk | Risk status | Within Company Risk Appetite |
| 1 | Report & HyperLink (Lean Open Banking) | Hyperlink misdirection exposing sensitive client data | No | Head of Product D&I - Alex | 31/01/2024 | Security | High | Mitigated | Validation between customer id , report id and lean app token should be in place so that one tpp can not fetch reports for someone else |  | Fully implemented | Low | Closed | Yes |
| 2 | Report & HyperLink (Lean Open Banking) | Outdated links used by clients causing data discrepancy | No | Head of Product D&I - Alex | 31.01.2024 | Operational | Medium | Mitigated | Expiration of hyperlinks  | Host validation should be in place for all new endpoints , if it is intended to be used on api host then other host should not be allowed to make request to those endpoints . | Fully implemented | Low | Closed | Yes |
| 3 | Report & HyperLink (Lean Open Banking) | Unauthorized sharing of generated report URLs outside corporate domain | No | Head of Product D&I - Alex | 31.01.2024 | Security | High | Mitigated | RBAC SOC24x7 usecase to cover user invite | MFA on user login | Fully implemented | Low | Closed | Yes |
| 4 | Report & HyperLink (Lean Open Banking) | Potential non-compliance with open banking regulations if reports show incorrect data | No | Chief Legal Officer | 31.01.2024 | Regulatory | Medium | Mitigated | Data consistency checks and IDOR checks | N/A | Fully implemented | Low | Closed | Yes |
| 5 | Corporate Lending Insights | Inconsistent data feeds from multiple sources impacting decision accuracy  | No | Head of Product D&I - Alex | 19.04.2024 | Data Integrity | Medium | Mitigated | Real-time validation and cross-source reconciliation Confidentiality requirements (Encryption in transit and encryption at rest, anonymization of sensitive data in logs) | N/A | Fully implemented | Low | Closed | Yes |
| 6 | Corporate Lending Insights | Unauthorized data exposure in lending analytics dashboards Integrity requirement (Input validation)  | No | Head of Product D&I - Alex | 19.04.2024 | Security | High | Mitigated | RBAC (Role-Based Access Control) and encryption at rest  | Authentication & Authorization (role based access controls, least privilege, object level authorization) | Fully implemented | Low | Closed | Yes |
| 7 | Corporate Lending Insights | Failure to meet corporate-lending compliance (e.g. cross-border rules) | No | Chief Legal Officer | 19.04.2024 | Regulatory | High | Mitigated | Regular compliance audits, legal sign-off for new markets | N/A | Fully implemented | Low | Closed | Yes |
| 9 | Retail Insights for Lenders | Data privacy risk from storing consumer credit info | No | Chief Legal Officer | 09.09.2024 | Privacy | High | Mitigated | Encryption at rest, strict data retention policies  | Host validation should be in place ( only api host should be able to make request to this endpoints ) | Fully implemented | Low | Closed | Yes |
| 10 | Retail Insights for Lenders | Misinterpretation of retail credit scores leading to wrong offers | No | Head of Product D&I - Alex | 09.09.2024 | Business/Process | Medium | Mitigated | Scoring model validations and workflow approvals  | Do not store PII data in any logs for this service such as Kibana  | Fully implemented | Low | Closed | Yes |
| 11 | Retail Insights for Lenders | Poor anonymization of transaction data used for analytics | No | Head of Product D&I - Alex | 09.09.2024 | Security | High | Mitigated | Tokenization, randomization of PII fields  | Do not store PII data in any logs for this service such as Kibana  | Fully implemented | Low | Closed | Yes |
| 12 | Retail Insights for Lenders | Unexpected surge in queries slowing performance | No | Head of Product D&I - Alex | 09.09.2024 | Operational | Medium | Mitigated | Load balancing | Autoscaling | Fully implemented | Low | Closed | Yes |
| 13 | AVS (IBAN Verification Service) | Third-party AVS API outage affecting onboarding flow | No | Head of Product D&I - Alex | 28.03.2024 | Vendor/3rd Party | High | Mitigated | SLA-based failover to secondary provider  | Perform input validation for all headers and params | Fully implemented | Low | Closed | Yes |
| 14 | AVS (IBAN Verification Service) | Inaccurate address data if provider database not updated | No | Head of Product D&I - Alex | 28.03.2024 | Data Integrity | Medium | Mitigated | Frequent syncs and periodic data quality checks | N/A | Fully implemented | Low | Closed | Yes |
| 15 | AVS (IBAN Verification Service) | Unencrypted request/response exposing addresses | No | Head of Product D&I - Alex | 28.03.2024 | Security | High | Mitigated | TLS 1.3, | Proper validation between entity id and lean app token should be in place  | Fully implemented | Low | Closed | Yes |
| 16 | AVS (IBAN Verification Service) | Non-compliance with Lean dev portal requirements | No | Head of Product D&I - Alex | 28.03.2024 | Regulatory | Medium | Mitigated | Regular reviews against Lean portal standards | N/A | Fully implemented | Low | Closed | Yes |
| 17 | Beneficiary Name (SAB AVS API) | Wrong beneficiary name mismatch leading to transfer issues | No | Head of Product D&I - Alex | 27.08.2024 | Data Integrity | Medium | Mitigated | Automated name verification & fallback checks Input validation should be in place for IBAN parameter  | N/A | Fully implemented | Low | Closed | Yes |
| 18 | Beneficiary Name (SAB AVS API) | Compromised tokens allowing unauthorized API calls | No | Head of Product D&I - Alex | 27.08.2024 | Security | High | Mitigated | Frequent token rotation | IP-based restrictions | Fully implemented | Low | Closed | Yes |
| 19 | Beneficiary Name (SAB AVS API) | Cross-region compliance conflict if certain data is shared | No | Chief Legal Officer | 27.08.2024 | Regulatory | High | Mitigated | Data privacy assessments when cross border processing may be requested  | Host validation should be in place for api endpoint and it should be only accessible from API host  | Fully implemented | Low | Closed | Yes |
| 20 | Beneficiary Name (SAB AVS API) | Lack of monitoring for name check requests leading to failed audits | No | Head of Product D&I - Alex | 27.08.2024 | Operational | Medium | Mitigated |  Error handling should be in place , error message should not revel anything sensitive in response. | API usage logging and real-time alerting | Fully implemented | Low | Closed | Yes |
| 21 | Insights via 3rd party (Mozn) | Inaccurate risk scores from third-party algorithm | No | Head of Product D&I - Alex | 06.02.2024 | Data Integrity | Medium | Mitigated | Regular calibration checks, SLA on data quality | N/A | Fully implemented | Low | Closed | Yes |
| 22 | Insights via 3rd party (Mozn) | Data leakage if sensitive PII is shared with the 3rd party | No | Chief Legal Officer | 06.02.2024 | Security | High | Mitigated | Encrypted transfers, restricted data fields  | Role based access control | Fully implemented | Low | Closed | Yes |
| 23 | Payout - Making Payments to End-Customers | Misconfigured payout instructions leading to funds sent to wrong accounts | No | Head of Products Payments - Kunal | 23.12.2024 | Operational | High | Mitigated | Dual authorization on payouts, IBAN validation  | Authentication & Authorization (role based access controls, least privilege, object level authorization) | Fully implemented | Low | Closed | Yes |
| 24 | Payout - Making Payments to End-Customers | Fraudulent payout requests exploiting system vulnerabilities | No | Head of Products Payments - Kunal | 23.12.2024 | Security | High | Mitigated | Transaction monitoring, anomaly detection rules Confidentiality requirements (Encryption in transit and encryption at rest, anonymization of sensitive data in logs)  | Integrity requirement (Input validation) | Fully implemented | Low | Closed | Yes |
| 25 | Refunds | Duplicate or incorrect refund amounts | No | Head of Products Payments - Kunal | 19.11.2024 | Business/Process | Medium | Mitigated | Automated checks, mandatory sign-off for large refunds  | Rate limiting should be in place at service level for POST /api/v1/payments/<payment_id>/refunds endpoint in order  to prevent many security issues such as creation of multiple beneficiaries under same customer id , or payment id | Fully implemented | Low | Closed | Yes |
| 26 | Refunds | Refund policy compliance failure (e.g. cross-border transactions) | No | Chief Legal Officer | 19.11.2024 | Regulatory | Medium | Mitigated | Legal review of refund flows, periodic audits Only allowed user roles should be able to perform this tasks such as Admin , Finance , Owner role etc for other user roles this functionality should not be visible . | N/A | Fully implemented | Low | Closed | Yes |
| 27 | Payment Status Tracking | Delayed status updates creating confusion for customers | No | Head of Products Payments - Kunal | 06.09.2024 | Operational | Medium | Mitigated | Polling and push notifications, clear SLAs | N/A | Fully implemented | Low | Closed | Yes |
| 28 | Payment Status Tracking | Incorrect post-initiation status leading to inconsistent records | No | Head of Products Payments - Kunal | 06.09.2024 | Data Integrity | High | Mitigated | Transaction logs cross-verification, real-time conflict resolution  | Object Level authorization rules are in place (e.g. an entity ID is tied to a user ID which is tied to lean app token) | Fully implemented | Low | Closed | Yes |
| 29 | Internal Billing Service | Overbilling or missed invoicing for partners | No | Head of Products Payments - Kunal | 28.01.2024 | Business/Process | Medium | Mitigated | Automated reconciliation scripts and monthly audit In case of data export from the tool only finance team should do it because it contains sensitive information about billing and data sharing about billing should follow best security practices such as sharing over one password with password protected zip file . | N/A | Fully implemented | Low | Closed | Yes |
| 30 | Internal Billing Service | Unauthorized adjustments to billing rates or discount structures | No | Head of Products Payments - Kunal | 28.01.2024 | Security | High | Mitigated | Role-based authorizations, audit trail on billing changes All of the endpoints will be secured using JWT tokens issued by our internal oauth service.: Backend validation should be in place for auth header which means in case of header modification or removal it should result into an 401 unauthorized error message   | Input validation and sanitization should be in place for all user input fields to avoid Owasp top 10 vulnerabilities | Fully implemented | Low | Closed | Yes |
| 31 | Payout service : Dashboard Payouts Initiation  | Unauthorized Approval of  payment by incorrect user role | No | Head of Products Payments - Kunal | 04.03.2025 | Security | High | Mitigated | Role-based authorizations for maker and checker role  | Proper JWT token validation, Feature flag in place , Privilage esclation related checks  | Fully implemented | Low | Closed | Yes |
| 32 | Subdomain takeover due to misconfigured domain  | Unauthorized Access of Lean subdomains  | No | Head of Devops - Illia | 04.03.2025 | Security | High | Mitigated | Attack surface monitoring in place which is integrated with slack channel  | Attack surface monitoring in place which is integrated with slack channel  | Fully implemented | Low | Closed | Yes |
| 33 | AVS - self serve | If AVS will be widely available, competitors or unqualified users such could sign up, such as individuals with access to test real data | No | Head of Product D&I - Alex | 10.03.2025 | Security | High | Mitigated | If abuse is detected, shift to invite-only mode. | Ensure only AVS APIs are available , by restricting the JWT claims | Not started | Low | Open | Yes |
| 34 | AVS - self serve | Users could repeatedly sign up under different emails to extend free access. |  | Head of Product D&I - Alex | 10.03.2025 | Commercial | High | Mitigated | Identify sign ups with the same company domain and manual checks where necessary. | Invite-only mode should be enforced by default | Not started | Low | Open | Yes |
| 35 | AVS - self serve | Potential that a non-SAMA regulated company could sign up to Lean and use AVS, would need to be reviewed by Compliance |  | Chief Legal Officer | 10.03.2025 | Compliance | High | Mitigated | If required to only enable for SAMA regulated companies we will shift to invite-only mode. | Invite-only mode should be enforced by default | Not started | Low | open | Yes |

## Security Controls List

| Policies for information security |
| --- |
| Review of the policies for information security |
| Information security roles and responsibilities |
| Segregation of duties |
| Contact with authorities |
| Contact with special interest groups |
| Information security in project management |
| Mobile device policy |
| Teleworking |
| Screening |
| Terms and conditions of employment |
| Management responsibilities |
| Information security awareness, education and training |
| Disciplinary process |
| Termination or change of employment responsibilities |
| Inventory of assets |
| Ownership of assets |
| Acceptable use of assets |
| Return of assets |
| Classification of information |
| Labelling of information |
| Handling of assets |
| Management of removable media |
| Disposal of media |
| Physical media transfer |
| Access control policy |
| Access to networks and network services |
| User registration and de-registration |
| User access provisioning |
| Management of privileged access rights |
| Management of secret authentication information of users |
| Review of user access rights |
| Removal or adjustment of access rights |
| Use of secret authentication information |
| Information access restriction |
| Secure log-on procedures |
| Password management system |
| Use of privileged utility programs |
| Access control to program source code |
| Policy on the use of cryptographic controls |
| Key management |
| Physical security perimeter |
| Physical entry controls |
| Securing offices, rooms and facilities |
| Protecting against external and environmental threats |
| Working in secure areas |
| Delivery and loading areas |
| Equipment siting and protection |
| Supporting utilities |
| Cabling security |
| Equipment maintenance |
| Removal of assets |
| Security of equipment and assets off-premises |
| Secure disposal or re-use of equipment |
| Unattended user equipment |
| Clear desk and clear screen policy |
| Documented operating procedures |
| Change management |
| Capacity management |
| Separation of development, test and operational facilities |
| Controls against malware |
| Information back-up |
| Event logging |
| Protection of log information |
| Administrator and operator logs |
| Clock synchronization |
| Installation of software on operational systems |
| Management of technical vulnerabilities |
| Restrictions on software installations |
| Information system audit controls |
| Network controls |
| Security of network services |
| Segregation in networks |
| Information transfer policies and procedures |
| Agreements on information transfer |
| Electronic messaging |
| Confidentiality or non-disclosure agreements |
| Information security requirements analysis and specification |
| Securing application services on public networks |
| Protecting application services transactions |
| Secure development policy |
| System change control procedures |
| Technical review of applications after operating system platform changes |
| Restrictions on changes to software packages |
| Secure system engineering principles |
| Secure development environment |
| Outsourced development |
| System security testing |
| System acceptance testing |
| Protection of test data |
| Information security policy for supplier relationships |
| Addressing security in supplier agreements |
| Information and communication technology supply chain |
| Monitoring and review of supplier services |
| Managing changes to supplier services |
| Responsibilities and procedures |
| Reporting information security events |
| Reporting security weaknesses |
| Assessment and decision of information security events |
| Response to information security incidents |
| Learning from information security incidents |
| Collection of evidence |
| Planning information security continuity |
| Implementing information security continuity |
| Verify, review and evaluate information security continuity |
| Availability of information processing facilities |
| Independent review of information security |
| Compliance with security policies and standards |
| Protection of records |
| Privacy and protection of personal identifiable information |
| Regulation of cryptographic controls |
| Independent review of information security |
| Compliance with security policies and standards |
| Technical compliance review |
| Defines security principles and guidelines to protect information assets. |
| Ensures security policies are updated periodically and aligned with regulations. |
| Defines security roles, responsibilities, and accountability across teams. |
| Prevents conflicts of interest by limiting access based on job roles. |
| Establishes communication channels with regulatory bodies for compliance. |
| Participation in cybersecurity forums and intelligence sharing communities. |
| Ensures security requirements are included from project initiation. |
| Defines security measures for mobile devices accessing corporate resources. |
| Establishes security controls for remote work environments. |
| Background verification of employees handling sensitive data. |
| Incorporates security obligations into employment contracts. |
| Defines executive responsibilities in security risk management. |
| Provides periodic training on phishing, social engineering, and compliance. |
| Defines consequences for violating security policies. |
| Ensures access is revoked promptly when employees leave or change roles. |
| Maintains a comprehensive list of IT assets for tracking and risk assessment. |
| Defines accountability for managing IT assets securely. |
| Defines acceptable and prohibited uses of IT resources. |
| Ensures return of company assets upon termination or role change. |
| Categorizes data based on sensitivity and regulatory requirements. |
| Ensures classified data is properly labeled (e.g., Confidential, Internal). |
| Defines protocols for managing and transferring sensitive data. |
| Restricts and monitors USB, external hard drives, and removable storage. |
| Ensures secure destruction of obsolete storage devices to prevent data leaks. |
| Defines security boundaries for data centers and restricted areas. |
| Enforces biometric or badge-based access restrictions to sensitive locations. |
| Protects physical workspaces from unauthorized access. |
| Mitigates risks from fire, floods, and power failures. |
| Restricts unauthorized personnel from entering critical zones. |
| Monitors external deliveries to prevent unauthorized access. |
| Defines user authentication and authorization mechanisms. |
| Restricts access to network resources based on need-to-know. |
| Manages user account provisioning and de-provisioning processes. |
| Implements least privilege access for system administrators. |
| Requires multi-factor authentication for accessing sensitive systems. |
| Periodically reviews and revokes unnecessary access privileges. |
| Enforces password complexity, expiration, and storage policies. |
| Restricts execution of administrative tools to authorized users. |
| Limits access to critical application source code repositories. |
| Defines encryption standards for data at rest and in transit. |
| Manages lifecycle of encryption keys to prevent unauthorized decryption. |
| Implements network firewalls, segmentation, and monitoring. |
| Monitors network traffic for malicious activities. |
| Collects security logs and alerts for anomaly detection. |
| Defines procedures for detecting, reporting, and responding to security incidents. |
| Monitors external threats and vulnerabilities affecting the organization. |
| Assesses security posture of third-party service providers. |
| Identifies and remediates software vulnerabilities. |
| Defines update cycles for security patches on systems and applications. |
| Monitors and responds to endpoint-based threats. |
| Centralizes log collection and real-time alerting. |
| Deploys antivirus and anti-malware solutions on endpoints. |
| Prevents unauthorized data transfers and exfiltration. |
| Ensures critical data and applications can be restored after an incident. |
| Conducts periodic disaster recovery and business continuity tests. |
| Defines secure coding practices for API authentication and access control. |
| Prevents injection attacks and input manipulation. |
| Mitigates DDoS attacks and abuse of services. |
| Restricts access based on geographic location. |
| Replaces sensitive data with anonymized tokens. |
| Integrates security checks into CI/CD pipelines. |
| Requires external audits and penetration testing of vendors. |
| Ensures TLS 1.3 and AES-256 encryption for data protection. |
| Grants access based on predefined roles and responsibilities. |
| Uses AI-driven monitoring for fraud and attack detection. |
| Validates consistency of stored data. |
| Ensures compliance with GDPR, DORA, UAE NESA, and other frameworks. |
| Verifies vendors comply with contractual security obligations. |
| Requires annual security training and phishing simulations. |
| Quarterly audits of privileged and sensitive accounts. |
| Validation between customer id, report id and lean app token should be in place so that one TPP cannot fetch reports for someone else |
| Versioning strategy and link expiration policies |
| Host validation should be in place for all new endpoints, if it is intended to be used on API host then other hosts should not be allowed to make requests to those endpoints |
| MFA on user login |
| Automated data checks and audit logs |
| Error handling in place which means during error messages do not reveal any sensitive information |
| Real-time validation and cross-source reconciliation |
| Confidentiality requirements (Encryption in transit and encryption at rest, anonymization of sensitive data in logs) |
| RBAC (Role-Based Access Control) and encryption at rest |
| Authentication & Authorization (role-based access controls, least privilege, object-level authorization) |
| Regular compliance audits, legal sign-off for new markets |
| Scheduled ETL runs with error-handling & backup processes |
| Respond with generic error messages and representative HTTP return code - avoid revealing details of the failure unnecessarily |
| Encryption at rest, strict data retention policies |
| Host validation should be in place (only API host should be able to make requests to these endpoints) |
| Scoring model validations and workflow approvals |
| Do not store PII data in any logs for this service such as Kibana |
| Tokenization, randomization of PII fields |
| Do not store PII data in any logs for this service such as Kibana |
| Load balancing, autoscaling triggers |
| SLA-based failover to secondary provider |
| Perform input validation for all headers and params |
| Perform host validation for the new API |
| Frequent syncs and periodic data quality checks |
| TLS 1.3, Proper validation between entity id and lean app token should be in place |
| Regular reviews against Lean portal standards |
| Automated name verification & fallback checks |
| Input validation should be in place for IBAN parameter |
| Frequent token rotation & IP-based restrictions |
| Geo-fencing, local data processing only |
| Host validation should be in place for API endpoint and it should be only accessible from API host |
| API usage logging and real-time alerting |
| Error handling should be in place, error messages should not reveal anything sensitive in response |
| Regular calibration checks, SLA on data quality |
| Encrypted transfers, restricted data fields |
| Role-based access control |
| Dual authorization on payouts, IBAN validation |
| Authentication & Authorization (role-based access controls, least privilege, object-level authorization) |
| Transaction monitoring, anomaly detection rules |
| Confidentiality requirements (Encryption in transit and encryption at rest, anonymization of sensitive data in logs) |
| Integrity requirement (Input validation) |
| Automated checks, mandatory sign-off for large refunds |
| Rate limiting should be in place at service level for POST /api/v1/payments/<payment_id>/refunds endpoint in order to prevent many security issues such as creation of multiple beneficiaries under same customer id, or payment id |
| Legal review of refund flows, periodic audits |
| Only allowed user roles should be able to perform these tasks such as Admin, Finance, Owner role etc. For other user roles this functionality should not be visible |
| Polling and push notifications, clear SLAs |
| Transaction logs cross-verification, real-time conflict resolution |
| Object Level authorization rules are in place (e.g. an entity ID is tied to a user ID which is tied to lean app token) |
| Automated reconciliation scripts and monthly audit |
| In case of data export from the tool only finance team should do it because it contains sensitive information about billing and data sharing about billing should follow best security practices such as sharing over OnePassword with password-protected zip file |
| Role-based authorizations, audit trail on billing changes |
| All of the endpoints will be secured using JWT tokens issued by our internal OAuth service |
| Backend validation should be in place for auth header which means in case of header modification or removal it should result in a 401 unauthorized error message |
| Input validation and sanitization should be in place for all user input fields to avoid OWASP Top 10 vulnerabilities |

## Assets

|  |  |  | Criticality |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Asset Name  | Asset Type | Example assets | Confidentiality | Integrity | Availability | Overall Criticality | Asset Owner | Role | Asset Owner Secondry | Role | Comments |
| Premises | Building | Premises, reception, fixture & fittings, alarms, CCTV, data processing areas, Main offices, dev centres, sales offices. | Low | Low | High | High | wafa.alamri@leantech.me | Office Manager KSA | aditya@leantech.me | CPO | Office Manager responsible for London office |
| Backups | Hardware | Backups of company held information (tapes, discs, server etc) | High | High | High | High | ashu@leantech.me  | CTO | damian@leantech.me DevOps Team | IT Manager DEvOps |  |
| Personal Computing equipment | Hardware | All standard laptop / desktop workstations | High | Low | Medium | High | ashu@leantech.me  | CTO | damian@leantech.me | IT Manager |  |
| Mobile Devices | Hardware | All mobile communication devices tablets, phones etc | Medium | Low | Low | Medium | ashu@leantech.me  | CTO | aditya@leantech.me | CPO |  |
| Removable Media | Hardware | USB, CDs &  DVDs | High | Low | Low | High | ashu@leantech.me  | CTO | damianr@leantech.me | IT Manager |  |
| Network Infrastructure | Hardware - Business Critical | Servers, Network Infrastructure etc including Production, Development systems (within co-location data centers) (Compute) | Critical | Low | Critical | Critical | oscar@leantech.me | Devops | illia.shpak@leantech.me | DevOps |  |
| Client data | Information | Client Data (including Client provided info), Incidents and personal data - covering B2B, KYC | Critical | Critical | High | Critical | ashu@leantech.me  | CTO | aditya@leantech.me | CPO |  |
| End-user data | Information | Personal data collected by client end users (financial information, no email addresses currently collected) | Critical | Critical | High | Critical | ashu@leantech.me  | CTO | aditya@leantech.me | CPO |  |
| Financial data | Information | Company Accounts (Financials), Billing/Invoicing | Critical | Critical | High | Critical | aditya@leantech.me  | CPO | Harryt@leantech.me | Head of Finance |  |
| Personal Data | Information | Staff Data, NI Number, Bank Details, Personnel records, Payroll, Expenses | Critical | Critical | High | Critical | Hisham@leantech.me | CEO | wendy@leantech.me | People Lead |  |
| Websites | Information | Company owned/leased websites (including Intranet; public sites) | Medium | Low | Medium | Medium | ashu@leantech.me  | CTO | aditya@leantech.me | CPO |  |
| Reputation | Intangiable  | Company Reputation  | Critical | Critical | Critical | Critical | Hisham@leantech.me | CEO | Ashu@leantech.me | CTO |  |
| Employees | People | Company Staff (Directors, Supervisors, Operational staff, HR), | High | High | High | High | aditya@leantech.me  | CPO | Wendy@leantech.me Marie@leantech.me | People Lead General Counsel |  |
| Third Parties | Services | Contractual obligations; contracts & SLAs; managed office providers, landlords cleaners, suppliers, etc | High | High | Medium | High | aditya@leantech.me  | CPO | Marie@leantech.me hisham@leantech.me | General Counsel CEO |  |
| Software & Development | Software and Microservices | Software employed in the business including bespoke software and application software. Software Development - Internal SDLC | Critical | Critical | Critical | Critical | ashu@leantech.me  | CTO | dragos@leantech.me | Head of Infosec |  |