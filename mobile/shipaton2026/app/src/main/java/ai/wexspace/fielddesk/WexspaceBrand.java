package ai.wexspace.fielddesk;

import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.view.View;

public final class WexspaceBrand {
    public static final int BG = Color.rgb(2,5,13);
    public static final int PANEL = Color.rgb(6,17,31);
    public static final int PANEL_2 = Color.rgb(8,25,45);
    public static final int CYAN = Color.rgb(34,230,255);
    public static final int BLUE = Color.rgb(18,92,255);
    public static final int ICE = Color.rgb(156,244,255);
    public static final int TEXT = Color.rgb(246,251,255);
    public static final int MUTED = Color.rgb(133,150,179);
    public static final int GREEN = Color.rgb(76,246,197);

    private WexspaceBrand() {}

    public static GradientDrawable panel(float radiusDp, float density) {
        GradientDrawable g = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{Color.rgb(8,27,50), Color.rgb(4,11,21)});
        g.setCornerRadius(radiusDp * density);
        g.setStroke(Math.max(1, Math.round(density)), Color.rgb(23,61,102));
        return g;
    }

    public static GradientDrawable pill(int stroke, int fill, float radiusDp, float density) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(radiusDp * density);
        g.setStroke(Math.max(1, Math.round(density)), stroke);
        return g;
    }

    public static void elevate(View v, float dp) {
        v.setElevation(dp * v.getResources().getDisplayMetrics().density);
    }
}
