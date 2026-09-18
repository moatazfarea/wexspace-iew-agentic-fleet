package ai.wexspace.fielddesk;

import android.app.Application;

public final class WexspaceApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        RevenueCatManager.initialize(this);
    }
}
