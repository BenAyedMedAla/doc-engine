---
source: [CSEC-D19] Incident Response Management Policy (v2.1).docx.pdf
parser: docling
pages: 22
gpu: True
---

<!-- image -->

<!-- image -->

## Incident Response Management Policy

## Table of Contents

| 1. Document Information                      |   3 |
|----------------------------------------------|-----|
| 1.1. Document Details                        |   3 |
| 1.2. Version Approval                        |   3 |
| 1.3. Version Control                         |   4 |
| 2. Purpose                                   |   5 |
| 3. Scope                                     |   5 |
| 4. Role and Responsibility                   |   6 |
| 5. Policy Statement                          |   7 |
| 6. Incident Response Process                 |   8 |
| 6.1. STEP 1: DETECTION AND ANALYSIS          |   9 |
| 6.1.1. Incident Detection                    |   9 |
| 6.1.2. Incident Analysis                     |  11 |
| 6.1.3. Incident Classification               |  12 |
| 6.1.4. Cyber Security Event Reporting        |  14 |
| 6.1.5. Cyber Security Incident Reporting     |  14 |
| 6.1.6. IMT Activation                        |  14 |
| 6.1.7. Incident Notifications                |  14 |
| 6.1.8. IMT Documentation                     |  15 |
| 6.1.9. Establishing Restricted Area for CERT |  16 |
| 6.2. STEP 2: CONTAINMENT AND ERADICATION     |  16 |
| 6.2.1. Resolution Action Plan                |  16 |
| 6.2.2. Evidence Preservation                 |  17 |
| 6.3. STEP 3: COMMUNICATIONS AND ENGAGEMENT   |  18 |
| 6.3.1. Internal Communications               |  18 |
| 6.3.2. External Communications               |  18 |
| 6.4. STEP 4: RECOVER                         |  19 |
| 6.4.1. Stand Down                            |  19 |
| 6.5. STEP 5: LEARN AND IMPROVE               |  19 |
| 6.5.1. Update Incident Response Plan         |  20 |
| 7. Review of the Document                    |  20 |
| 8. Compliance and Non-Compliance             |  20 |
| 9. Related Documents                         |  21 |

<!-- image -->

<!-- image -->

3

## 1.  Document Information

## 1.1.  Document Details

| Document Number         | CSEC-D19                            |
|-------------------------|-------------------------------------|
| Document Name           | Incident Response Management Policy |
| Document Owner          | Cyber Security                      |
| Document Reviewer       | Cyber Security GRC Specialist       |
| Document Approver       | Director of Cyber Security          |
| Document Classification | Confidential                        |
| Version Number          | 2.1                                 |
| Version Date            | 28 th September 2025                |

## 1.2.  Version Approval

|   Ver. # | Date        | Approver Name   | Approver Role          | Signature   |
|----------|-------------|-----------------|------------------------|-------------|
|      2.1 | 30 Sep 2025 | Rakan Alassaf   | Head of Cyber Security |             |

<!-- image -->

## 1.3.  Version Control

|   Ver. # | Ver. Date     | Change Description/ Reason                                                                                            | Created / Revised by                                                                                | Approved by          |
|----------|---------------|-----------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|----------------------|
|      1.0 | 13 -Oct- 2021 | Initial Version                                                                                                       | An Hoang                                                                                            | Abdulmajeed Alsukhan |
|      1.1 | 23 -Aug- 2022 | Minor Changes/Annual Review                                                                                           | Yousuf Almuallem                                                                                    | Rakan Alassaf        |
|      1.2 | 31 -May- 2023 | Refined Policy Statement                                                                                              | Yousuf Almuallem                                                                                    | Rakan Alassaf        |
|      2.0 | 2 9-Jun- 2024 | Annual Review Major Update : Updated Section 4 & Section 6.1.1. Added 6.1.7 Establishing Restricted Area for CERT     | Qaiser Sajjad Saif Ur Rehman Isaac Farooq ( External Auditors ) Abdulaziz Alshehri Yousuf Almuallem | Rakan Alassaf        |
|      2.1 | 28-Sep-2025   | Annual Review : Minor editorial updates, including formatting, terminology adjustments. No substantive policy changes | Alya Alshaikh Yousuf Almualem                                                                       | Rakan Alassaf        |

<!-- image -->

<!-- image -->

## 2.  Purpose

Threats, vulnerability or intrusions to information systems infrastructure including environmental or utility disruptions, human error or malicious attacks. Irrespective of the motivation or cause of the incident whether intentional or unintentional or any suspected or confirmed attempt to compromise or disrupt the integrity, availability or confidentiality of customer data shall be immediately reported and managed in accordance with the incident response plan and reporting procedures.

For risks related to incident management (IM), Tamara recognizes that it is essential to make a fundamental commitment to information security a first-order mission or business requirement.

The purpose of this policy is to clearly define IT roles and responsibilities for the investigation and response of computer security incidents and Data Breaches.

## 3.  Scope

This policy applies to all users of information assets, information owners and information custodians collectively referred to as 'Users' including:

- Tamara employees.
- Employees of temporary employment agencies.
- Customers are utilizing testing facilities, business recovery invocation, and Resources.
- Vendors.
- Business partners, and contractor personnel,
- Functional units regardless of geographic locations.

This policy covers all Information Systems (IS) environments operated by Tamara or contracted with a third party for use by Tamara.

Although this policy explicitly covers the responsibilities of information users, owners, and custodians, it shall be read and applied in conjunction with other Tamara Cyber Security policies, standards, and procedures.

All users must read, understand and comply with this plan and other relevant Information Security policies, standards, and procedures.

If any employee or user does not fully understand anything in these documents, he/she should consult with his/her manager or human resources, who can contact the Security Team for further clarification if necessary.

<!-- image -->

<!-- image -->

## 4.  Role and Responsibility

The following section details the composition and functions of the Tamara Incident Management Team (IMT) and the Senior Executive Management Team (SEMT).

| Name                   | Title                                | Mobile           | Email                        |
|------------------------|--------------------------------------|------------------|------------------------------|
| Chien Hoang            | Engineering VP                       | +49 1520 6013774 | chien.hoang@tamara.co        |
| Abdulmohsen Al Babtain | Chief Product Officer (CPO)          | +966 50 321 1136 | abdulmohsen@tamara.co        |
| Sudheesh Kumar         | Product VP                           | +971 58 532 6001 | sudheesh.kumar@tamara.co     |
| Rakan Alassaf          | Cybersecurity Manager                | +966 50 424 2353 | rakan.alassaf@tamara.co      |
| An Hoang               | Cyber Security Senior Engineer II    | +84 0707 007101  | an.hoang@tamara.co           |
| Abdulaziz Alshehri     | Cyber Security Senior Engineer       | +966 55 830 7847 | abdulaziz.alshehri@tamara.co |
| Yousuf Almuallem       | Security Associate Engineer          | +966 54 731 2899 | yousuf.almuallem@tamara.co   |
| Bill Sayedsayedhegazy  | Engineering Manager - Infrastructure | +66 658501000    | bill.hegazy@tamara.co        |
| Srikanth Hari          | Incident Management Lead             | +91 9036 741667  | srikanth.hari@tamara.co      |
| Chung Nguyen           | Senior Engineering Manager           | +49 1633 673255  | chung.nguyen@tamara.co       |
| Faisal Boday           | Compliance Manager                   | +966501782888    | faisal.boday@tamara.co       |

<!-- image -->

<!-- image -->

## 5.  Policy Statement

- The effectiveness of this process should be measured and annually evaluated.
- The Objective of this policy is to ensure timely identification and handling of cyber security incidents in order to reduce the (potential) business impact on Tamara's business.
- This process will address different security events that should be responded to, such as malware infections, DDOS attacks, and the unavailability of data centers .
- In case of incidents, certified forensic companies will be engaged to investigate and handle the incidents.
- In case of incidents, all required support should be provided to the Computer Emergency Response Team (CERT).
- All incidents reported must go through the Enterprise Incident Logging Process , which includes logging through Jira and other CERT requirements.
- All related evidence and logs should be protected.
- Root cause analysis should be performed to learn the lesson and implement preventive controls.
- CISO should track the implementation of corrective actions post incidents.
- All incidents should be logged into incident logs.
- Tamara will inform 'SAMA IT Risk Supervision' immediately when a medium or high classified security incident has occurred and is identified.
- Tamara will obtain 'no objection' from 'SAMA IT Risk Supervision' before any media interaction related to the incident.
- Tamara will submit a formal incident report, 'SAMA IT Risk Supervision' after resuming operations, including the following incident details:
- o Title of incident &amp; Classification (medium or high)
- o Date and time of incident occurred &amp; detected
- o Information assets involved
- o Technical details of the incident
- o Root-cause analysis
- o Corrective activities performed and planned
- o Description of impact (e.g., loss of data, disruption of services, unauthorized modification of data, (un)intended data leakage, number of customers impacted)
- o Total estimated cost of the incident
- o Estimated cost of corrective actions
- Tamara has sufficient internal staff with expertise to handle major incidents and has established relationships with external forensic teams to supplement our resources when needed.
- Tamara may use an outsourced SOC service for monitoring. In such cases, the following is mandatory:

<!-- image -->

<!-- image -->

<!-- image -->

- o An agreement between Tamara and an outsourced SOC Team must be established.
- o Tamara must ensure that a monitoring process is in place and approved by Tamara.
- o The monitoring process must follow regulatory requirements.
- o An Incident Response Process (IRP) must be established, and Tamara must approve it.
- Tamara must establish and periodically review SOC Roles and Responsibilities &amp; Hierarchy.
- Tamara's IM process requires SOC analysts to be skilled and continuously train staff.
- This policy is associated with Tamara's Cyber Security Event Management policy. Refer to the Related Documents section for more information.
- The Cyber Security Department shall conduct periodic reviews of cybersecurity controls for incident management every year.

## 6. Incident Response Process

Quick Reference Checklist of Incident Response Actions

|   No | Activity                                                                                                                                                 |
|------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
|    1 | Analyze to determine whether an incident has occurred / or is occurring.                                                                                 |
|    2 | Determine the incident's scope, impact and severity; categorize the incident.                                                                            |
|    3 | Activate your IMT (and SEMT, if appropriate) to manage the response effort; begin documenting the situation.                                             |
|    4 | Develop and implement a resolution action plan detailing containment, eradication and recovery activities; gather and record evidence.                   |
|    5 | Identity-affected stakeholders - who will be impacted by the incident?                                                                                   |
|    6 | Develop a notifications strategy and communicate key messages with affected stakeholders.                                                                |
|    7 | Confirm the threat has been eradicated and return affected systems/services to normal function (test systems/services to confirm expected functionality) |
|    8 | Stand down your IMT/SEMT (when authorized by the appropriate delegate) and determine any stakeholder communications requirements.                        |

<!-- image -->

<!-- image -->

|   No | Activity                                                                                                                             |
|------|--------------------------------------------------------------------------------------------------------------------------------------|
|    9 | Conduct a post-incident review to identify what worked well and any opportunities for improvement; document your learnings/insights. |
|   10 | Update your incident response plan to include any key learnings/insights.                                                            |

## 6.1. STEP 1: DETECTION AND ANALYSIS

## 6.1.1. Incident Detection

There is no single process for detecting a cyber-incident. Detection often involves:

- Precursors: detecting that a cyber-attack might occur in the future, such as receiving a threatening email or news of a global malware/ransomware attack (note: this form of detection is rare).
- Indicators: detection that an incident may have occurred (e.g. intrusion detection alerts, file names with odd characters, configuration changes).
- Security Monitoring: A referral from a managed security service provider or another organization/stakeholder alerting to the presence of a cyber-incident.

The table below provides some common indicators that suggest you might be experiencing a cyber-security incident.

| Indicators                                                                   | Examples                                                                                                                                                                                    |
|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Reports of unusual or suspicious activity by staff or external stakeholders. | A staff member receives an email asking them to confirm their network credentials or to provide other personal or sensitive information.                                                    |
| Reports of unusual or suspicious activity by staff or external stakeholders. | Multiple staff report being 'locked out' of their network accounts.                                                                                                                         |
| Reports of unusual or suspicious activity by staff or external stakeholders. | An external stakeholder reports receiving spam or phishing emails from your organization.                                                                                                   |
| Reports of unusual or suspicious activity by staff or external stakeholders. | A member of the public approaches your organization to report the discovery (or exploitation) of a security vulnerability.                                                                  |
| System(s)/service(s) not operating or functioning as expected                | For example, one or more IT systems or services may cease functioning or may not function as expected, and there is not a readily identifiable cause (such as a planned upgrade or outage). |
| System(s)/service(s) not operating or functioning as expected                | SSL Certificates broke; customers complain that your organization's website has a broken link.                                                                                              |

<!-- image -->

<!-- image -->

| Unusual Activity   | Network administrators observe a large number of 'bounced' emails containing suspicious or unexpected content, or there is a substantial change in network traffic flows with no readily identifiable cause.   |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Unusual Activity   | Network or application logs show multiple failed login attempts from unfamiliar remote systems, such as overseas locations.                                                                                    |
| Unusual Activity   | Anti-virus alerts - a notification from your anti-virus service or a managed service provider that it has detected suspicious activity or files on your network, which require analysis and remediation.       |
| Unusual Activity   | Service or admin accounts modify permissions; admin accounts add standard users to groups; service accounts log into a workstation.                                                                            |
| Unusual Activity   | A system administrator observes a filename with unusual characters or expected files are no longer visible on the network.                                                                                     |

## Other suspicious events are as follows:

1. Unusual Network Traffic Patterns:
- Sudden spikes or anomalies in network traffic could indicate a potential cyber attack, such as a distributed denial-of-service (DDoS) attack or unauthorized data exfiltration.
2. Unexplained Account Activities:
- Anomalous login attempts, failed authentication, or account lockouts may indicate unauthorized access attempts or credential-stuffing attacks.
3. Unexpected File Changes:
- Unauthorized modifications or deletions of critical system files, configuration files, or user data may signal a compromise or malware infection.
4. Abnormal System Behavior:
- Unexplained system crashes, slowdowns, or freezes could indicate malware activity, system compromise, or resource exhaustion attacks.
5. Security Policy Violations:
- Instances of users attempting to bypass security controls, escalate privileges, or access restricted resources may indicate insider threats, malicious intent, or policy non-compliance.
6. Suspicious Outbound Connections:
- Outbound connections to known malicious IP addresses, command and control servers, or suspicious domains may suggest malware communication or data exfiltration attempts.
7. Phishing Attempts:
- Receipt of suspicious emails containing malicious attachments, links to phishing websites, or requests for sensitive information may indicate phishing attacks targeting employees or users.
8. Unexpected Software Installs:

<!-- image -->

<!-- image -->

- Installation of unauthorized software or applications on company devices without proper authorization may signify unauthorized access or insider threats.

## 9. Failed Security Control Checks:

- Detection of failed security control checks, such as antivirus scans, intrusion detection/prevention system (IDS/IPS) alerts, or firewall rule violations, may indicate attempted security breaches or malware activity.

## 10. Anomalous User Behavior:

- Abnormal user activity patterns, such as accessing unusual files or directories, performing unauthorized system commands, or accessing resources outside their normal behavior profile, could indicate compromised accounts or insider threats.

## 11. Data Access Anomalies:

- Unusual or unauthorized access to sensitive data, databases, or file shares, especially during non-business hours or from unfamiliar locations, may suggest data breaches or insider misuse.

## 12. Unexplained System Privilege Escalation:

- Instances of unauthorized users gaining escalated privileges or administrative access to systems or applications without proper authorization may indicate security policy violations or advanced persistent threats (APTs).

## 13. Unexpected External Connections:

- Establishment of unauthorized external connections to company systems or devices, such as unauthorized remote access sessions or VPN connections from unknown sources, may indicate unauthorized access attempts or compromise of external-facing services.

## 14. Unusual DNS Activity:

- Suspicious DNS requests, such as queries for known malicious domains, DNS tunnelling attempts, or excessive DNS traffic volume, may indicate malware infections or command and control communication.

## 6.1.2. Incident Analysis

After considering the indicators of a potential cyber incident, it is important to confirm whether an incident has occurred or continues to occur. The following table identifies steps that are useful in confirming the presence of a cyber incident.

<!-- image -->

<!-- image -->

| Action                                                                    | Description                                                                                                                                                                                                                                                         |
|---------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Updated Resources                                                         | Ensure you have access to the latest: - Network diagrams - IP addressing schemas - Port lists - Documentation that may include system designs/architecture, security plans, GPO configuration, etc.                                                                 |
| Reviewing log entries and security alerts                                 | Are there any unusual entries or signs of suspicious behaviour on the network or applications?                                                                                                                                                                      |
| Have Standard Operating Procedures (SOPs) for different operating systems | For Windows workstations, follow an SOP on what to look for or review (i.e. specific event log sources, the types of events to search for, etc.). The same applies to Linux and Unix Operating Systems.                                                             |
| Consult with network and application experts.                             | Is there a legitimate explanation for the unusual or suspicious activity that has been observed?                                                                                                                                                                    |
| Conduct research                                                          | Research and review any open source materials (including via internet search engines) relating to the unusual or suspicious activity observed (for example, consider performing a search on any unusual filenames observed on the network).                         |
| Watch list/monitor list.                                                  | Develop a list where suspected accounts or IPs can be added to monitor their ongoing activity.                                                                                                                                                                      |
| IMPORTANT                                                                 | Do not 'ping' or try to communicate with a suspected IP address or URL from your network, as you may tip off the attacker that you have detected their activity. This should be conducted by a third party that can perform this activity securely and anonymously. |

It is important to consider the timeliness of your analysis. While lengthy analysis is useful for developing a comprehensive understanding of an incident, it can also impede the overall response process.

Generally, spending up to one hour on the initial incident analysis phase is advisable before seeking outside assistance.

## 6.1.3. Incident Classification

The following table provides a guide for classifying a cyber-incident and provides indicators to consider when determining whether its impact and severity are increasing or decreasing.

<!-- image -->

<!-- image -->

| Category                                                                                                                                                                                                                                                                                                                                                                                                  | Description                                                                                                                                                                                                                                                                                                                                                                | Trigger(s) for escalation   |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| A suspected (or unconfirmed) cyber incident with no observable impact on systems or services.                                                                                                                                                                                                                                                                                                             | Substantial increase in cyber security alerts or continued cyber security alerts with the potential to breach security controls. Confirmed breach of security controls.                                                                                                                                                                                                    | Cyber Event                 |
| Successful compromise of security controls that requires corrective action. Minor to moderate impact on services, information, assets, reputation or relationships. It may form part of a national or international cyber incident.                                                                                                                                                                       | Actual or high likelihood: ● For major impact on services; or ● To affect multiple organizations; or ● Data breach involving personal information.                                                                                                                                                                                                                         | Cyber Incident              |
| action. Major to significant impact on services, information, assets, government reputation, relationships and/or the community (but not an emergency). Any incident that involves: ● More than one organization; or ● A data breach involving personal information.                                                                                                                                      | A situation that: ● Has the potential to cause or is causing loss of life and extensive damage to property, infrastructure or the environment or ● Has the potential to have or is having significant adverse consequences for the Tamara community or a part of the Tamara community. Immediately refer all significant cyber incidents and cyber emergencies to the IMT. | Significant Cyber Incident  |
| Successful compromise of security controls that: ● Has the potential to cause or is causing loss of life and extensive damage to property, infrastructure or the environment; or ● Has the potential to have or is having significant adverse consequences for the Tamara community or a part of the Tamara community; or ● Requires the involvement of two or more agencies to respond to the emergency. |                                                                                                                                                                                                                                                                                                                                                                            | Cyber Emergency             |

<!-- image -->

## 6.1.4. Cyber Security Event Reporting

| Service         | Severity          | Notification Time   | Response Time                       | Resolution Time                     | SLA Applicability                   |
|-----------------|-------------------|---------------------|-------------------------------------|-------------------------------------|-------------------------------------|
| Event Reporting | Critical          | 30 minutes          | 30 minutes 4                        | hours 24x7x365                      |                                     |
| Event Reporting | High              | 45 minutes          | 45 minutes 8                        | hours                               |                                     |
| Event Reporting | Medium            | 60 minutes          | 1 day 2 days                        | hours 24x7x365                      |                                     |
| Event Reporting | Low               | 60 minutes          | 2 days 4 days                       | hours 24x7x365                      |                                     |
| Event Reporting | Alerting Method → | Alerting Method →   | Phone Call / Email ←→ Jira ←→ Slack | Phone Call / Email ←→ Jira ←→ Slack | Phone Call / Email ←→ Jira ←→ Slack |

Notification Time :

Time to notify Tamara

Response Time :

Time for Tamara to respond

## 6.1.5. Cyber Security Incident Reporting

| Service            | Severity                                        | Response Time   | Resolution Time   | SLA Applicability   |
|--------------------|-------------------------------------------------|-----------------|-------------------|---------------------|
| Incident Reporting | Critical                                        | 30 minutes      | 4 hours 24x7x365  |                     |
| Incident Reporting | High                                            | 45 minutes      | 8 hours           |                     |
| Incident Reporting | Medium 90                                       | minutes         | 2 days            |                     |
| Incident Reporting | Low                                             | 120 minutes     | 4 days            |                     |
| Incident Reporting | Alerting Method → Phone Call / Email ←→ Jira ←→ | Slack           | Slack             | Slack               |

## 6.1.6. IMT Activation

If a cyber-incident is confirmed and requires a team to manage the response effort, activate the IMT (note: some more minor incidents may be manageable without activation of the IMT).

## 6.1.7. Incident Notifications

It is essential to notify relevant stakeholders that a cyber-incident has occurred or is occurring. The incident's scope, impact and severity should determine the extent of stakeholder notifications. More severe incidents will likely require engagement with a broader range of stakeholders.

<!-- image -->

<!-- image -->

<!-- image -->

Key stakeholders to notify include:

- [list relevant organizational senior executive and their contact details]
- [list relevant government departments or agencies (including regulators) based on your circumstances]

The IMT, typically via the Incident Manager or communications lead, is responsible for managing these notifications on behalf of Tamara.

[Consider developing a list or table that identifies the stakeholders relevant to each category of cyber incident]

## 6.1.8. IMT Documentation

Upon establishment, the IMT should immediately begin documenting information about the incident. This documentation includes 'situation updates' ( and the 'incident log' .

Situation updates should contain the following information:

- Incident date and time (usually the date and time the incident was confirmed)
- The status of the incident - for example, new / in progress / resolved
- Incident type and classification - for example, malware/ransomware / DDoS etc.
- Scope - details of affected networks, systems and/or applications
- Impact - details of entities affected by the incident and how they are affected
- Severity - details of the impact of the incident on the organization(s) (for example, what business services are impacted?)
- Contact details for the incident manager and key IMT personnel.

Situation updates should be prepared and disseminated to Tamara's internal stakeholders regularly. It is important to be proactive in developing and disseminating your situation reports to reduce the need for stakeholders to approach you with various questions about the incident. A member of the IMT (or a delegate) should maintain the incident log. The log should capture minutes from each IMT meeting, details of all critical decisions (including the rationale for a decision), operational actions taken, action items, and future meeting dates and times. Each entry should include the date, time, and author details.

<!-- image -->

<!-- image -->

## 6.1.9. Establishing Restricted Area for CERT

## 1. Identify Suitable Location:

- Select a secure and accessible location within the organization's premises to establish the CERT workspace. Consider proximity to critical infrastructure, ease of access for team members, and physical security measures.

## 2. Implement Physical Security Measures:

- Implement physical security measures to restrict access to the CERT workspace. This may include access control systems, biometric authentication, security cameras, and secure locks on doors and windows.

## 3. Establish Secure Access Controls:

- Define access control policies and procedures to govern entry into the CERT workspace. Only authorized personnel, such as members of the CERT team and designated IT staff, should be granted access.

## 4. Equip the Workspace:

- Furnish the CERT workspace with the necessary equipment and resources to support incident response activities. This may include desks, chairs, computers, monitors, telecommunication equipment, network infrastructure, and storage facilities for documentation and tools.

## 5. Ensure Connectivity and Power Supply:

- Ensure reliable connectivity to the organization's network and internet services within the CERT workspace. Additionally, backup power sources, such as uninterruptible power supplies (UPS) or generators, must be provided to maintain operations during power outages.

## 6. Implement Environmental Controls:

- Implement environmental controls to maintain suitable conditions within the CERT workspace. This includes temperature regulation, ventilation, and protection against environmental hazards such as dust, moisture, and electromagnetic interference.

## 7. Regular Maintenance and Testing:

- Conduct regular maintenance checks and testing of equipment, infrastructure, and security controls within the CERT workspace to ensure readiness for incident response activities. Periodically test communication channels, connectivity, and backup systems.

## 6.2.  STEP 2: CONTAINMENT AND ERADICATION

## 6.2.1. Resolution Action Plan

The IMT should develop a Resolution Action Plan to resolve the incident.

The Resolution Action Plan should consider the immediate and future steps required to contain the incident and eradicate any threats that might exist, as well as the future steps required to restore systems and services. The Resolution Action Plan should be reviewed throughout the process, as it may change depending on what evidence is acquired during the detection and analysis steps.

<!-- image -->

<!-- image -->

<!-- image -->

The key elements of the Resolution Action Plan are:

- Containment actions - what are you doing now to contain the incident/threat and prevent the spread of the situation?
- Eradication actions - what are you doing to remove the incident/threat from your environment?
- Capability and capacity requirements - what resources do you require for the plan to be successful?
- Communications actions - what messages are you communicating, to whom, when and how?

The details of the Resolution Action Plan will vary depending on the type of incident that you experience. There is no 'one size fits all' approach.

When developing the Resolution Action Plan, it is essential to consider:

- How long will it take to resolve the incident?
- What resources are required to resolve the incident (if not included in the IMT)?
- What systems/services will be affected during the resolution process? What services are impacted?

## 6.2.2. Evidence Preservation

The IMT will collect and record evidence about the cyber incident to support detailed forensic investigations, including law enforcement efforts to identify and prosecute potential cyber-attackers.

To the best of its ability, and where relevant to the incident, the IMT should collect and record the following evidence:

- Hard drive images and raw images
- RAM images
- IP addresses
- Network packet captures and flows
- Network diagrams
- Log and configuration files
- Databases
- IR/investigation notes
- Screenshots
- Social media posts
- CCTV, video and audio recordings
- Documents detailing the monetary cost of remediation or loss of business activity.

When gathering evidence, it is essential to consider the following steps:

- Nominate a member of the IMT to be responsible for collating, recording and storing all collected evidence.
- The IMT will create and maintain a log of all collected evidence, detailing the date and time it was collected, who it was collected by, and details of each item collected.

<!-- image -->

<!-- image -->

<!-- image -->

- Ensure that all evidence is securely stored and handled only by the nominated IMT member, with limited access provided to other staff.
- Any access to evidence should be recorded in the evidence log, including the rationale for access. This is important in maintaining the 'chain of custody' for collected evidence.
- Minimize the number of times evidence is transferred between staff. Record details of any evidence transfer between staff.

## 6.3.  STEP 3: COMMUNICATIONS AND ENGAGEMENT

## 6.3.1. Internal Communications

Beyond the regular situation reports, it may be necessary to brief your organization's employees about a cyber-incident. This is important if organizational IT networks, systems, or applications no longer operate as expected or if the situation has the potential to generate media or public interest.

Key messages to consider when communicating with employees include:

- What happened, and why did it happen?
- What will happen in the immediate future?
- What are employees expected to do?
- Who can employees contact if they have questions?

All internal communications must be reviewed and approved by &lt;communications lead and the Incident Manager&gt; prior to release.

## 6.3.2. External Communications

Depending on the impact and severity of a cyber-incident, it may be necessary to communicate with external stakeholders (including ministers, media, and the public). This is particularly important if the incident affects IT networks, systems, or applications relied upon by third parties, such as public-facing websites or services.

Key messages to consider when communicating with external stakeholders include:

- What happened, and why did it happen?
- What systems/services are affected?
- What steps are being taken to resolve the situation?
- Is it possible to say when the situation will be resolved?
- What are external stakeholders expected to do?
- Who can external stakeholders contact if they have questions/concerns?

All external communications must be reviewed and approved by &lt;communications lead and the Incident Manager&gt; prior to release. If the SEMT is activated, the SEMT Chair should approve all external communications prior to release.

<!-- image -->

## 6.4.  STEP 4: RECOVER

The IMT should develop a plan to recover from the cyber incident.

The recovery plan should detail the approach to recovering IT networks, systems (sysops/DevOps) and applications once containment and eradication are complete. Depending on the type and severity of an incident, the IMT may need to develop this plan in conjunction with business continuity and IT services advisors.

The recovery plan should include the following elements:

- A plan to restore systems to regular operation.
- A process of continual monitoring to confirm that the affected systems are functioning normally.
- A plan (if applicable) to remediate vulnerabilities to prevent similar incidents.

It is essential to consider that, in some circumstances, a recovery plan may include finalizing a related criminal investigation (including forensic evidence collection), which may need to occur before recovery is possible.

## 6.4.1. Stand Down

Following the implementation and execution of an agreed recovery plan, the Incident Manager should advise the IMT that it is acceptable to stand down.

If the SEMT is activated, only the SEMT Chair (or Deputy Chair) should issue stand-down instructions after consulting with the Incident Manager.

The Incident Manager should gather copies of all notes taken during the response effort to assist with a Post Incident Review.

## 6.5.  STEP 5: LEARN AND IMPROVE

This step is one of the most important phases in the incident response process, yet it is also the one that is most often overlooked. Learning from each incident enables the IMT to continually improve its processes and procedures for managing cyber incidents.

The IMT (and SEMT, if activated) should come together for a Post Incident Review to discuss:

- Exactly what happened, and at what times?
- How well did staff and management perform in dealing with the incident? Were the documented procedures followed? Were they adequate?
- What information was needed sooner?
- Were any steps or actions taken that might have inhibited the recovery?
- What would the staff and management do differently the next time a similar incident occurs?
- How could information sharing with other organizations have been improved?
- What corrective actions can prevent similar incidents in the future?
- What future precursors or indicators should be watched for to detect similar incidents?
- What additional tools or resources are needed to detect, analyze, and mitigate future incidents?

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

The discussion should be documented, and any key insights/lessons learnt should be shared with all parties involved. Any recommendations that arise from the discussion should be documented in a corresponding action plan that states how the recommendation will be actioned, by whom, and when.

The suggested improvements shall be presented to CISO, IMT, and the Cyber Security Committee for review and necessary approval.

## 6.5.1. Update Incident Response Plan

This plan will be continually updated to reflect better cyber incident response activities practices, including following any relevant post-incident reviews.

## 7. Review of the Document

This document, including any policies, standards, guidelines, or procedures, will be reviewed on an annual basis, and as needed , to ensure its continued relevance, effectiveness, and alignment with evolving regulatory requirements, business objectives, and emerging cyber threats. The review process will involve key stakeholders to assess and update the content as necessary to maintain the highest standards of cybersecurity within Tamara.

## 8. Compliance and Non-Compliance

Compliance with this document will be measured and verified through various methods, including but not limited to periodic audits, assessments, and monitoring activities that adhere to relevant Personal Data Protection Laws, SAMA, NCA, and ISO/IEC 27001 standards. These methods may include business and cybersecurity intelligence reports, internal and external audits, and feedback from document owners. All compliance activities will be conducted with due regard to privacy and data protection requirements.

Any exceptions to this document must be formally documented and pre-approved by the Chief Information Security Officer (CISO) and at least one other C-level executive within Tamara. Any employee found to have violated this document may be subject to disciplinary action, up to and including termination of employment, in line with the Tamara's disciplinary procedures and relevant legal and regulatory frameworks.

## 9.  Related Documents

- [CSEC-D18] Cyber Security Event Management
- Enterprise Incident Management Procedures

<!-- image -->

<!-- image -->

REF. NUMBER MOJ62-OBBHA-UXMXI-5FARR

## SIGNER

## TIMESTAMP

| RAKANALASSAF            | SENT 30   | SEP    |   2025 | 19:05:12   |
|-------------------------|-----------|--------|--------|------------|
| EMAIL                   | VIEWED    | VIEWED |        |            |
| RAKAN.ALASSAF@TAMARA.CO | 30        | SEP    |   2025 | 19:08:21   |
|                         | SIGNED    | SIGNED |        |            |
|                         | 30        | SEP    |   2025 | 19:09:28   |

RECIPIENT VERIFICATION

<!-- image -->

EMAIL VERIFIED 30 SEP 2025 19:08:21

SIGNATURE

<!-- image -->

IP ADDRESS

78.95.240.148

LOCATION

RIYADH, SAUDI ARABIA

DOCUMENT COMPLETED BY ALL PARTIES ON 30 SEP 2025 19:09:28 UTC

<!-- image -->