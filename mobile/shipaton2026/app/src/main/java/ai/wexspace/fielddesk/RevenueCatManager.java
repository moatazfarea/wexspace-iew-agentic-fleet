package ai.wexspace.fielddesk;

import android.app.Activity;
import android.content.Context;

import androidx.annotation.NonNull;

import com.revenuecat.purchases.CustomerInfo;
import com.revenuecat.purchases.LogLevel;
import com.revenuecat.purchases.Offerings;
import com.revenuecat.purchases.PurchaseCallback;
import com.revenuecat.purchases.PurchaseParams;
import com.revenuecat.purchases.Purchases;
import com.revenuecat.purchases.PurchasesConfiguration;
import com.revenuecat.purchases.PurchasesError;
import com.revenuecat.purchases.ReceiveCustomerInfoCallback;
import com.revenuecat.purchases.ReceiveOfferingsCallback;
import com.revenuecat.purchases.Store;
import com.revenuecat.purchases.StoreTransaction;
import com.revenuecat.purchases.galaxy.GalaxyBillingMode;

import java.util.List;

public final class RevenueCatManager {
    public static final String PRO_ENTITLEMENT = "pro";
    private static boolean configured = false;

    private RevenueCatManager() {}

    public static void initialize(Context context) {
        String key = BuildConfig.REVENUECAT_API_KEY == null ? "" : BuildConfig.REVENUECAT_API_KEY.trim();
        if (key.isEmpty()) return;

        Purchases.setLogLevel(BuildConfig.DEBUG ? LogLevel.DEBUG : LogLevel.INFO);

        PurchasesConfiguration.Builder builder = new PurchasesConfiguration.Builder(context, key);
        if ("GALAXY".equals(BuildConfig.REVENUECAT_STORE)) {
            builder.store(Store.GALAXY);
            builder.galaxyBillingMode(BuildConfig.DEBUG ? GalaxyBillingMode.TEST : GalaxyBillingMode.PRODUCTION);
        } else {
            builder.store(Store.TEST_STORE);
        }
        Purchases.configure(builder.build());
        configured = true;
    }

    public static boolean isConfigured() {
        return configured;
    }

    public interface StatusCallback {
        void onResult(boolean pro, String message);
    }

    public static void refreshProStatus(StatusCallback callback) {
        if (!configured) {
            callback.onResult(false, "RevenueCat key not configured for this build.");
            return;
        }
        Purchases.getSharedInstance().getCustomerInfo(new ReceiveCustomerInfoCallback() {
            @Override
            public void onReceived(@NonNull CustomerInfo customerInfo) {
                boolean active = customerInfo.getEntitlements().getActive().containsKey(PRO_ENTITLEMENT);
                callback.onResult(active, active ? "WEXSPACE Pro active" : "Free plan active");
            }

            @Override
            public void onError(@NonNull PurchasesError error) {
                callback.onResult(false, "Billing status unavailable: " + error.getMessage());
            }
        });
    }

    public static void purchaseFirstPackage(Activity activity, StatusCallback callback) {
        if (!configured) {
            callback.onResult(false, "RevenueCat is not configured yet.");
            return;
        }
        Purchases.getSharedInstance().getOfferings(new ReceiveOfferingsCallback() {
            @Override
            public void onReceived(@NonNull Offerings offerings) {
                if (offerings.getCurrent() == null) {
                    callback.onResult(false, "No current offering is configured.");
                    return;
                }
                List<com.revenuecat.purchases.Package> packages = offerings.getCurrent().getAvailablePackages();
                if (packages == null || packages.isEmpty()) {
                    callback.onResult(false, "No packages are available in the current offering.");
                    return;
                }

                com.revenuecat.purchases.Package selected =
                        offerings.getCurrent().getMonthly() != null
                                ? offerings.getCurrent().getMonthly()
                                : packages.get(0);

                Purchases.getSharedInstance().purchase(
                        new PurchaseParams.Builder(activity, selected).build(),
                        new PurchaseCallback() {
                            @Override
                            public void onCompleted(@NonNull StoreTransaction transaction, @NonNull CustomerInfo info) {
                                boolean active = info.getEntitlements().getActive().containsKey(PRO_ENTITLEMENT);
                                callback.onResult(active,
                                        active ? "Purchase verified. Pro unlocked."
                                                : "Purchase completed, but Pro entitlement is not active.");
                            }

                            @Override
                            public void onError(@NonNull PurchasesError error, boolean userCancelled) {
                                callback.onResult(false,
                                        userCancelled ? "Purchase cancelled."
                                                : "Purchase failed: " + error.getMessage());
                            }
                        }
                );
            }

            @Override
            public void onError(@NonNull PurchasesError error) {
                callback.onResult(false, "Could not load offering: " + error.getMessage());
            }
        });
    }

    public static void restore(StatusCallback callback) {
        if (!configured) {
            callback.onResult(false, "RevenueCat is not configured yet.");
            return;
        }
        Purchases.getSharedInstance().restorePurchases(new ReceiveCustomerInfoCallback() {
            @Override
            public void onReceived(@NonNull CustomerInfo customerInfo) {
                boolean active = customerInfo.getEntitlements().getActive().containsKey(PRO_ENTITLEMENT);
                callback.onResult(active, active ? "Purchases restored. Pro active." : "No Pro entitlement found.");
            }

            @Override
            public void onError(@NonNull PurchasesError error) {
                callback.onResult(false, "Restore failed: " + error.getMessage());
            }
        });
    }
}
