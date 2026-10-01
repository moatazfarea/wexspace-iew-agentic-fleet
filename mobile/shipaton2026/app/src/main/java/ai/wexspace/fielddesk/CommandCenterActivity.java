package ai.wexspace.fielddesk;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public final class CommandCenterActivity extends Activity {
    private int dp(int v){ return Math.round(v*getResources().getDisplayMetrics().density); }

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);
        setContentView(build());
        RevenueCatManager.refreshProStatus((pro,msg)->runOnUiThread(()->billing.setText(pro?"WEXSPACE PRO · ACTIVE":"WEXSPACE PRO · READY")));
    }

    private TextView billing;

    private View build(){
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(WexspaceBrand.BG);
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(20),dp(20),dp(20),dp(42));scroll.addView(root);

        LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setPadding(0,0,0,dp(14));
        ImageView logo=new ImageView(this);logo.setImageResource(R.drawable.wexspace_logo);logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo,new LinearLayout.LayoutParams(dp(74),dp(74)));
        LinearLayout titleBox=new LinearLayout(this);titleBox.setOrientation(LinearLayout.VERTICAL);titleBox.setPadding(dp(12),0,0,0);
        TextView title=text("WEXSPACE AI",26,true,WexspaceBrand.TEXT);titleBox.addView(title);
        TextView sub=text("COMMAND CENTER · HUMAN-GOVERNED EXECUTION",10,true,WexspaceBrand.CYAN);titleBox.addView(sub);
        header.addView(titleBox,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        root.addView(header);

        TextView hero=text("One workspace.\nMany specialist missions.",34,true,WexspaceBrand.TEXT);hero.setLineSpacing(0,0.95f);root.addView(hero);
        TextView desc=text("Durable project state · specialist routing · evidence-linked results · exact human authority boundaries.",15,false,WexspaceBrand.MUTED);
        desc.setPadding(0,dp(10),0,dp(16));root.addView(desc);

        LinearLayout state=card(); state.setPadding(dp(16),dp(14),dp(16),dp(14));
        LinearLayout stateTop=new LinearLayout(this);stateTop.setGravity(Gravity.CENTER_VERTICAL);
        TextView live=text("●  LIVE WORKSPACE",11,true,WexspaceBrand.GREEN);stateTop.addView(live,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        billing=text("WEXSPACE PRO · READY",10,true,WexspaceBrand.CYAN);stateTop.addView(billing);
        state.addView(stateTop);
        TextView pipeline=text("REQUEST   →   SPECIALIST   →   TOOL   →   EVIDENCE",11,true,WexspaceBrand.ICE);pipeline.setPadding(0,dp(13),0,0);state.addView(pipeline);
        root.addView(state,margin(0,0,0,dp(18)));

        root.addView(label("ACTIVE PROJECTS"));
        root.addView(projectCard("01","MECHANICAL ENGINEERING","UTL-NET-001 · Cooling Water Network","Deterministic hydraulics + independent verification","OPEN ENGINEERING",v->startActivity(new Intent(this,EngineeringActivity.class))),margin(0,0,0,dp(12)));
        root.addView(projectCard("02","SOFTWARE / GOVERNANCE QA","Request Scope Gate · RCS","Acceptance criteria, evidence and human release boundary","OPEN QA",v->startActivity(new Intent(this,MainActivity.class))),margin(0,0,0,dp(12)));
        root.addView(projectCard("03","STUDIO OS","Production Job #001","60fps capture, cinematic timeline, evidence and QA","OPEN STUDIO",v->startActivity(new Intent(this,StudioActivity.class))),margin(0,0,0,dp(18)));

        root.addView(label("EXECUTION FABRIC"));
        LinearLayout fabric=card();fabric.setPadding(dp(16),dp(16),dp(16),dp(16));
        fabric.addView(text("Configured  ≠  Authorized  ≠  Executed  ≠  Verified",13,true,WexspaceBrand.ICE));
        TextView f=text("Every project shares the same durable state, agent/tool provenance and explicit human authority model.",12,false,WexspaceBrand.MUTED);f.setPadding(0,dp(8),0,0);fabric.addView(f);
        root.addView(fabric,margin(0,0,0,dp(16)));

        LinearLayout pro=card();pro.setPadding(dp(16),dp(16),dp(16),dp(16));
        pro.addView(text("✦  WEXSPACE PRO",12,true,WexspaceBrand.CYAN));
        pro.addView(text("RevenueCat-backed entitlement for premium evidence capabilities.",13,false,WexspaceBrand.TEXT));
        LinearLayout actions=new LinearLayout(this);actions.setPadding(0,dp(10),0,0);
        Button unlock=button("Unlock Pro");unlock.setOnClickListener(v->RevenueCatManager.purchaseFirstPackage(this,(p,m)->runOnUiThread(()->billing.setText(p?"WEXSPACE PRO · ACTIVE":m))));
        Button restore=button("Restore");restore.setOnClickListener(v->RevenueCatManager.restore((p,m)->runOnUiThread(()->billing.setText(p?"WEXSPACE PRO · ACTIVE":m))));
        actions.addView(unlock,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));actions.addView(restore,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));
        pro.addView(actions);root.addView(pro);

        return scroll;
    }

    private LinearLayout projectCard(String num,String lane,String name,String body,String cta,View.OnClickListener click){
        LinearLayout card=card();card.setPadding(dp(18),dp(18),dp(18),dp(18));card.setOnClickListener(click);WexspaceBrand.elevate(card,4);
        LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);
        TextView n=text(num,12,true,WexspaceBrand.CYAN);n.setBackground(WexspaceBrand.pill(Color.rgb(27,76,124),Color.rgb(5,22,40),9,getResources().getDisplayMetrics().density));n.setPadding(dp(9),dp(6),dp(9),dp(6));top.addView(n);
        TextView l=text(lane,10,true,WexspaceBrand.MUTED);l.setPadding(dp(10),0,0,0);top.addView(l);card.addView(top);
        TextView h=text(name,20,true,WexspaceBrand.TEXT);h.setPadding(0,dp(14),0,0);card.addView(h);
        TextView p=text(body,13,false,WexspaceBrand.MUTED);p.setPadding(0,dp(6),0,dp(14));card.addView(p);
        TextView go=text(cta+"  →",11,true,WexspaceBrand.ICE);card.addView(go);
        return card;
    }

    private LinearLayout card(){
        LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setBackground(WexspaceBrand.panel(18,getResources().getDisplayMetrics().density));return l;
    }
    private TextView label(String s){TextView v=text(s,10,true,WexspaceBrand.CYAN);v.setPadding(0,dp(7),0,dp(9));return v;}
    private TextView text(String s,int sp,boolean bold,int color){TextView v=new TextView(this);v.setText(s);v.setTextSize(sp);v.setTextColor(color);if(bold)v.setTypeface(null,android.graphics.Typeface.BOLD);return v;}
    private Button button(String s){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setTextColor(WexspaceBrand.TEXT);b.setBackground(WexspaceBrand.pill(Color.rgb(30,83,135),Color.rgb(8,32,58),10,getResources().getDisplayMetrics().density));return b;}
    private LinearLayout.LayoutParams margin(int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
}
