package ai.wexspace.fielddesk;

public final class HydraulicEngine {
    private static final double G = 9.80665;
    private static final double RHO = 997.0;
    private static final double MU = 0.00089;

    public static final class Segment {
        public final String id;
        public final double lengthM, diameterMm, roughnessMm, flowM3h, kLocal, elevationM;
        public Segment(String id,double lengthM,double diameterMm,double roughnessMm,double flowM3h,double kLocal,double elevationM){
            this.id=id;this.lengthM=lengthM;this.diameterMm=diameterMm;this.roughnessMm=roughnessMm;
            this.flowM3h=flowM3h;this.kLocal=kLocal;this.elevationM=elevationM;
        }
    }

    public static final class Result {
        public final String id;
        public final double velocity, reynolds, friction, dropKpa;
        Result(String id,double velocity,double reynolds,double friction,double dropKpa){
            this.id=id;this.velocity=velocity;this.reynolds=reynolds;this.friction=friction;this.dropKpa=dropKpa;
        }
    }

    private HydraulicEngine(){}

    private static double swameeJain(double re,double rr){
        if(re<2300.0) return 64.0/re;
        return 0.25/Math.pow(Math.log10(rr/3.7+5.74/Math.pow(re,0.9)),2);
    }

    private static double haaland(double re,double rr){
        if(re<2300.0) return 64.0/re;
        return Math.pow(-1.8*Math.log10(Math.pow(rr/3.7,1.11)+6.9/re),-2);
    }

    public static Result calculate(Segment s, boolean independent){
        double d=s.diameterMm/1000.0, eps=s.roughnessMm/1000.0, q=s.flowM3h/3600.0;
        double area=Math.PI*d*d/4.0, v=q/area, re=RHO*v*d/MU, rr=eps/d;
        double f=independent?haaland(re,rr):swameeJain(re,rr);
        double vh=v*v/(2.0*G);
        double total=(f*s.lengthM/d+s.kLocal)*vh+s.elevationM;
        double drop=RHO*G*total/1000.0;
        return new Result(s.id,v,re,f,drop);
    }

    public static Segment[] demoNetwork(){
        return new Segment[]{
            new Segment("S-001",20,100,0.045,30,1.2,1),
            new Segment("S-002",30,65,0.045,18,3.5,4),
            new Segment("S-003",25,50,0.045,12,4.0,2)
        };
    }

    public static boolean verify(Result primary,Result independent){
        double rel=Math.abs(independent.dropKpa-primary.dropKpa)/Math.max(Math.abs(primary.dropKpa),1e-12);
        return rel<=0.05;
    }
}
