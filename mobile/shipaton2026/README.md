# WEXSPACE FieldDesk — Shipaton 2026 isolated mobile delta

Status: **isolated development branch — not a canonical WEXSPACE promotion and not a submitted/frozen competition mutation**.

## Product
WEXSPACE FieldDesk is a mobile-first governed evidence workbench for engineers and field professionals. A user defines a bounded work item, acceptance criteria, and grounded evidence. A deterministic gate computes criterion coverage, while final release remains human-controlled.

This is intentionally more than a WebView port:
- mobile evidence capture/import with SHA-256 evidence fingerprints;
- criterion-to-evidence binding;
- deterministic coverage gate;
- explicit human release boundary;
- RevenueCat entitlement path for Pro features;
- Galaxy Store-specific production billing path.

## Billing architecture
Two build flavors keep development and production truthfully separated:
- `sandboxDebug`: RevenueCat Test Store, using `REVENUECAT_TEST_API_KEY`.
- `galaxyDebug` / `galaxyRelease`: Samsung Galaxy Store via `purchases-store-galaxy`, using `REVENUECAT_GALAXY_API_KEY`. Debug uses Galaxy TEST billing mode; release uses PRODUCTION.

No API key is committed.

## Build
Requires JDK 17, Android SDK 36, Gradle 9.6+, and AGP 9.4.

```bash
cd mobile/shipaton2026
gradle :app:testSandboxDebugUnitTest :app:assembleSandboxDebug
gradle :app:assembleGalaxyDebug
```

## Proposed Galaxy Store identity
- App title: **WEXSPACE FieldDesk**
- Package: `ai.wexspace.fielddesk.samsung`
- Version: `0.1.0`
- Category candidate: Productivity / Business
- Monetization: free download + Pro subscription.
- Shipaton: new mobile release during the submission window.

## Release gates
A release build is not considered ready until:
1. Samsung Commercial Seller Status is provider-approved.
2. The package is registered in Seller Portal.
3. Galaxy Store app is connected to RevenueCat using the official service account flow.
4. Real Galaxy products/entitlement/offerings are configured.
5. `galaxyRelease` uses a `galx_` public SDK key, never a Test Store key.
6. A physical Galaxy device or Samsung-approved test surface verifies billing and entitlement behavior.
7. Store listing, privacy disclosures, screenshots, age rating, and review metadata are complete.
8. Publication/readback is verified from the provider.
