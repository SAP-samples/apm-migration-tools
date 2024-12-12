# Introduction
The legacy products SAP PDMS (Predictive Maintenance and Service, SAP ASPM (Asset Strategy and Performance Management),
SAP PAI (Predictive Asset Insights) or
SAP APM based on SAP IoT (Asset Performance Management) have been sunset by SAP in 2022, 2023 and 2024 so that new customers cannot buy these products anymore.
The alternative to PDMS, PAI and ASPM and the successor to APM based on SAP IoT is APM based on Embedded IoT made generally available in October 2024.
This guide intends to show the way to customers, partners and involved SAP personell how this migration can be done commercially and technically.
# Audience and Contribution
This guide is meant for everyone driving or participating in the migration to APM based on Embedded IoT.
This guide is continously updated by the dedicated APM migration coaches that work with customers that are productive on the legacy products to coach them in the migration. But it might also be relevant to customers and partners that have not yet been fully productive with the legacy products or that are implementing the new APM architecture and are knowledgeable about the legacy products.
At the customer this might be the Reliability Engineer that wants to understand the functional differences and the implications to his data,
the IT person that wants to understand the necessary technical steps and plan the migration or
the buer that wants to understand how entitlements and costs change with the new product.
The partner might be an implementation partner chosen by the customer to support the migration,
a software partner that provides complementary software,
a software partner that provides components of APM
or a reseller that sells APM.
The SAP personell is the account executive who needs to negotiate the new license terms and conditions with the customer buyer,
the customer success partner who helps the customer with adopting this and other DSC (Digital Supply Chain) solutions,
the 
Your contribution to this guide is very much appreciated by the SAP APM community so please feel free to create issues or to even create pull requests if you want to correct or enhance it.
# Migration Scenarios

```mermaid
graph TD;
    PDMS-->APM-eiot;
    PAI-->APM-eiot;
    ASPM-->APM-eiot;
    APM-siot-->APM-eiot;
```
# Migration Steps - APM-siot to APM-eiot without usage of Asset Health features
- [x] Customer IT and evtl partner read this guide
- [ ] Customer IT and SAP customer success partner to project future usage
- [ ] Customer Buyer swap license with SAP account executive from 8012342 to 8019182
- [ ] Wait for tenant copy/swap to become available
- [ ] Create a ticket to copy/swap your tenant
