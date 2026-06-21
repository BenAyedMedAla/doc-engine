---
source: Risk acceptance evidence1.png
parser: vlm
model: Qwen/Qwen3.6-27B-FP8
pages: 1
---

Here is the full analysis of the provided Jira ticket page:

---

**Document Type**: Jira Issue (Task/Story)  
**Project**: Likely “SEC” (based on issue key SEC-702)  
**Issue Key**: SEC-702  
**Title**: Integration of PRS with self-MFA service(a.k.a Amr service) without k8s authentication mechanism in place  
**Status**: Approved (as shown in dropdown)  
**Assignee**: Aditya Sarkar  
**Reporter**: Dragos Dabija  
**Created**: January 24, 2023 at 8:56 AM  
**Updated**: February 7, 2023 at 10:02 AM  
**Residual Security Risk**: Low  
**Risk Acceptance Expiration Date**: Mar 10, 2023  

---

### **Description Summary**

The ticket describes a required integration between two services:
- **Payment Reconciliation Service (PRS)**
- **self-MFA service (also called Amr service)**

This integration is needed to enable automatic refreshing of transactions for pre-authorised bank accounts. Specifically, when a `reconnect_required` status is received, PRS must be able to generate the required **otp token**.

However, this integration is being implemented **without Kubernetes (k8s) authentication mechanisms in place**, which violates previously agreed security requirements.

---

### **Why Risk Acceptance is Requested (by Product Team)**

Two main reasons are given:

1. **Security Requirement Violation**: Authentication between PRS and self-MFA service was supposed to be in place on production (ae01), but it won’t be — due to technical constraints.
2. **Business Urgency**: One client is actively looking to use the automatic PRS flow ASAP.

---

### **Additional Context**

- Security requirements were defined ahead of implementation as part of the Secure SDLC approach (link referenced as “here”).
- Requirements were discussed and agreed upon with engineering teams.
- All security requirements were successfully implemented and tested on environments ae03 and ae02 (security epic linked).
- Promotion to production (ae01) failed because ae01 runs a lower version of Kubernetes that doesn’t support the sidecar implementation needed for token-based auth between PRS and self-OTP service.
- DevOps plans to fix this misalignment within 6 weeks (by March 10, 2023).

---

### **Right Panel Details**

#### **Development**
- Create branch
- Create commit

#### **TestRail Integration**
- TestRail: Cases → Open TestRail: Cases
- TestRail: Runs → Open TestRail: Runs

#### **More Fields**
- Original estimate, Time tracking, Parent (collapsed)

#### **Automation**
- Rule executions (collapsed)

#### **Zendesk Support**
- Linked Tickets (collapsed)

---

### **Bottom Section**

- **Residual Risk Score Description**: Section header present, but no content visible below it in the screenshot.
- **Comment Box**: “Add a comment...” with quick reply suggestions (“Suggest a reply...”, “Status update...”, “Thanks...”)

---

### **Top Navigation & UI Elements**

- Browser URL: `leantechnologies.atlassian.net`
- Jira top menu: Your work, Projects, Filters (active), Dashboards, Teams, Plans, Assets, Apps, Create button
- Search bar with 9+ notifications
- User profile icon, settings gear, help icon

---

### **Key Observations & Implications**

✅ **Risk Accepted Temporarily**: The team has formally accepted the residual risk until March 10, 2023, allowing deployment despite missing k8s auth.

⚠️ **Technical Debt / Misalignment**: Production environment (ae01) lags behind dev/test environments (ae02/ae03) in Kubernetes version, blocking proper security implementation.

🔁 **DevOps Action Required**: A 6-week timeline is set to resolve the k8s version mismatch — critical for long-term security compliance.

📌 **Client Pressure**: Business need is driving the exception — highlighting tension between security policy and delivery timelines.

🔗 **Traceability**: Links to TestRail cases/runs and security epic suggest good traceability and testing coverage despite the workaround.

---

### **Recommendations (if applicable)**

1. **Monitor Deadline**: Ensure DevOps delivers the k8s upgrade by March 10, 2023.
2. **Compensating Controls**: Consider temporary compensating controls (e.g., network segmentation, logging, monitoring) to mitigate risk during the gap.
3. **Post-Mortem**: After resolution, document lessons learned to prevent future environment misalignments.
4. **Communicate Stakeholders**: Inform product and security teams about progress toward remediation.

---

This ticket reflects a real-world scenario where business urgency overrides strict security adherence — a common challenge in agile environments — and demonstrates structured risk acceptance with clear ownership and deadlines.