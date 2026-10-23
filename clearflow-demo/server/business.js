// ClearFlow Plumbing is a fictional business for a JT Builds Co demo.
// This file is the ONLY source of business facts. The website, the demo
// assistant and the live AI prompt all read from it, so the assistant can
// never state a service, area, hour or policy that isn't written here.

export const BUSINESS = {
  name: "ClearFlow Plumbing",
  shortName: "ClearFlow",
  fictional: true,
  phone: "(555) 014-7720",
  phoneHref: "tel:+15550147720",
  email: "hello@clearflowplumbing.example",
  region: "Denver metro, Colorado",
  licensed: "Licensed and insured plumbers",

  services: [
    { id: "leak", name: "Leak detection & repair", blurb: "Hidden leaks found and fixed, from slab leaks to dripping supply lines.", keywords: ["leak", "leaking", "drip", "dripping", "slab", "wet spot", "water stain"] },
    { id: "drain", name: "Drain cleaning", blurb: "Kitchen, bath and main-line clogs cleared and checked.", keywords: ["drain", "clog", "clogged", "slow drain", "backed up", "backup", "snake", "hydro"] },
    { id: "water-heater", name: "Water heater repair & installation", blurb: "Tank and tankless water heaters repaired, replaced and installed.", keywords: ["water heater", "hot water", "tankless", "heater", "no hot water"] },
    { id: "sewer", name: "Sewer line inspection & repair", blurb: "Camera inspections and sewer line repairs.", keywords: ["sewer", "sewer line", "camera", "main line", "root", "roots"] },
    { id: "fixtures", name: "Fixture & faucet installation", blurb: "Faucets, sinks, toilets, showers and garbage disposals installed.", keywords: ["faucet", "sink", "toilet", "shower", "tub", "fixture", "disposal", "garbage disposal"] },
    { id: "repipe", name: "Repiping", blurb: "Whole-home and partial repipes for aging or failing pipes.", keywords: ["repipe", "repiping", "old pipes", "galvanized", "polybutylene", "pipe replacement"] },
    { id: "sump", name: "Sump pump service", blurb: "Sump pump repair, replacement and installation.", keywords: ["sump", "sump pump", "basement pump"] },
    { id: "emergency", name: "Emergency plumbing", blurb: "Burst pipes, major leaks and sewer backups, 24/7.", keywords: ["emergency", "burst", "flood", "flooding"] },
  ],

  areas: ["Denver", "Aurora", "Lakewood", "Englewood", "Littleton", "Arvada", "Wheat Ridge", "Golden"],

  hours: [
    { days: "Monday – Friday", time: "7:00 AM – 6:00 PM" },
    { days: "Saturday", time: "8:00 AM – 2:00 PM" },
    { days: "Sunday", time: "Closed for scheduled work" },
  ],

  emergency: {
    available: "24/7, including nights, weekends and holidays",
    covers: ["burst pipes", "major leaks", "sewer backups", "no water to the home"],
    howTo: "Call the emergency line at (555) 014-7720. Emergency calls go straight to the on-call plumber.",
  },

  policies: {
    pricing: "ClearFlow doesn't quote prices over chat. A licensed plumber looks at the job and gives you a written estimate before any work starts.",
    followUp: "The dispatch team reviews new requests during business hours and calls you back to schedule. For an emergency, call the 24/7 line instead.",
  },
};

export const SERVICE_NAMES = BUSINESS.services.map((s) => s.name);
