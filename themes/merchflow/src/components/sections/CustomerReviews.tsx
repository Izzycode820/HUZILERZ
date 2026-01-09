import React from "react";
import { Star, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const REVIEWS = [
    {
        id: 1,
        name: "Sandra Farmer",
        role: "Assistant Manager",
        image: "https://placehold.co/100x100/A78BFA/FFFFFF/png?text=SF",
        text: "We were so happy with the way our apron turned out! We ordered this for our friend's bachelorette party and it needed to be shipped to Canada and processed through customs. I was afraid it wasn't going to get here in time..."
    },
    {
        id: 2,
        name: "Chloe Knowles",
        role: "Sales Manager",
        image: "https://placehold.co/100x100/F59E0B/FFFFFF/png?text=CK",
        text: "I've just received them today and I love them! Super fast and friendly service and they feel like amazing quality, I'm sure my partner will love them."
    },
    {
        id: 3,
        name: "Tiahne Case",
        role: "Sales Manager",
        image: "https://placehold.co/100x100/EC4899/FFFFFF/png?text=TC",
        text: "Item was perfect - you get a picture of what it will look like before they ship. Very quick and helpful responses. I would highly recommend!"
    },
    {
        id: 4,
        name: "Kari Morrisey",
        role: "Graphic Designer",
        image: "https://placehold.co/100x100/34D399/FFFFFF/png?text=KM",
        text: "They were a gift for my husband with our dog face on them and he loves them. He got many compliments showing them off at work. Will be ordering more, for sure."
    },
    {
        id: 5,
        name: "James Brackett",
        role: "Office Manager",
        image: "https://placehold.co/100x100/60A5FA/FFFFFF/png?text=JB",
        text: "So cute! Got this for my pet loving best friend and she was overjoyed. The print quality is fantastic and has held up well after washing."
    },
    {
        id: 6,
        name: "Lala Sloney",
        role: "Receptionist",
        image: "https://placehold.co/100x100/F87171/FFFFFF/png?text=LS",
        text: "Our second year of new sock tradition for xmas gifts from the boys to dad continues! Great quality, cute prints, and fast shipping."
    },
    {
        id: 7,
        name: "Jonathan Winnie",
        role: "Instructional Designer",
        image: "https://placehold.co/100x100/818CF8/FFFFFF/png?text=JW",
        text: "Item arrived within the time that it was estimated and the quality was great. My mom was in tears and said it was her favorite gift of the year."
    },
    {
        id: 8,
        name: "Lisa Lydon",
        role: "Graphic Designer",
        image: "https://placehold.co/100x100/F472B6/FFFFFF/png?text=LL",
        text: "The printing looks to be good quality! Very detailed and accurate colors matching the design file I uploaded. Impressed."
    }
];

export function CustomerReviews() {
    return (
        <section className="py-24 bg-gradient-to-b from-purple-50 to-white relative overflow-hidden">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

            <div className="container mx-auto px-4 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-4xl font-bold text-gray-900 mb-4 uppercase tracking-wide">Customer Reviews</h2>
                    <p className="text-gray-600 mb-4">We do everything we can to ensure a positive merchant experience.</p>
                    <div className="flex items-center justify-center gap-2">
                        <span className="text-[#4ADE80] font-bold text-xl">4.9/5</span>
                        <div className="flex text-yellow-400">
                            {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
                        </div>
                        <span className="text-gray-500 font-medium ml-2">Trusted by 199,087 Clients</span>
                    </div>
                </div>

                {/* Masonry-like Grid */}
                <div className="columns-1 md:columns-2 lg:columns-4 gap-6 space-y-6">
                    {REVIEWS.map((review) => (
                        <div key={review.id} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 break-inside-avoid hover:shadow-md transition-shadow">
                            <div className="flex items-center gap-3 mb-4">
                                <img src={review.image} alt={review.name} className="w-10 h-10 rounded-full" />
                                <div>
                                    <div className="flex items-center gap-1">
                                        <h4 className="font-bold text-gray-900 text-sm">{review.name}</h4>
                                        <CheckCircle className="w-3 h-3 text-green-500" />
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <p className="text-xs text-gray-400">{review.role}</p>
                                        <div className="flex text-yellow-400">
                                            {[...Array(5)].map((_, i) => <Star key={i} className="w-2 h-2 fill-current" />)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <p className="text-gray-600 text-sm leading-relaxed">
                                "{review.text}"
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
