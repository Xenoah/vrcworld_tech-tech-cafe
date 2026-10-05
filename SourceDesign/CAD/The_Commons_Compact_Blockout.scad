
// THE COMMONS - Compact Edition
// Concept blockout, units = mm. Not construction documentation.
$fn = 48;
W=28000; D=18000; wall=250; h1=4800; h2=4800; roof=200;

module wall_box(x,y,w,d,h,z=0){ translate([x,y,z]) cube([w,d,h]); }
module slab(x,y,w,d,z,t=200){ translate([x,y,z]) cube([w,d,t]); }
module stage(){ translate([14000,13200,0]) cylinder(h=250,r=2400); }

// 1F floor
slab(0,0,W,D,-200,200);
// shell walls with entrance gap
wall_box(0,0,11500,wall,h1+h2);
wall_box(16500,0,W-16500,wall,h1+h2);
wall_box(0,D-wall,W,wall,h1+h2);
wall_box(0,0,wall,D,h1+h2);
wall_box(W-wall,0,wall,D,h1+h2);

// 2F side mezzanines; preserve central atrium
slab(0,4200,8800,12600,h1-100,200);
slab(19800,1000,8200,15800,h1-100,200);
slab(8800,15300,11000,2250,h1-100,200);
slab(8800,2600,11200,2400,h1-100,200);

// stage and DJ booth massing
stage();
slab(11000,12600,6000,3200,h1-100,200);
wall_box(11200,13000,5600,200,1400,h1+200);

// major internal masses
wall_box(500,4400,7000,250,2600); // bar back line
wall_box(23000,7200,250,8400,2600); // poster spine
wall_box(21700,1000,250,5400,2600); // quiet nook edge

// roof
slab(0,0,W,D,h1+h2,roof);
