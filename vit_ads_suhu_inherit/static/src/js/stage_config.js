/** @odoo-module **/

export const STAGES = [
    { id: "vit.product_value_analysis", label: "Product Value Analysis" },
    { id: "vit.market_mapper", label: "Market Mapper" },
    { id: "vit.audience_profiler", label: "Audience Profiler" },
    { id: "vit.angle_hook", label: "Angle" },
    { id: "vit.hook", label: "Hook" },
    { id: "vit.ads_copy", label: "Ads Copy" },
    { id: "vit.image_generator", label: "Images", parent: "vit.ads_copy", hidden: true },
    { id: "vit.video_generator", label: "Videos", parent: "vit.ads_copy", hidden: true },
    { id: "vit.script_writer", label: "Script Writer" },
    { id: "vit.visual_concept", label: "Visual Concept" },
    { id: "vit.compliance_checker", label: "Compliance Checker" },
    { id: "vit.landing_page_builder", label: "Landing Page Builder" },
    { id: "vit.campaign_builder", label: "Campaign Builder" },
];

export const getStageImageSrc = (resModel) =>
    `/vit_ads_suhu_inherit/static/src/img/${resModel}.png`;
