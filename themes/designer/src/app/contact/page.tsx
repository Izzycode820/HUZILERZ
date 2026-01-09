"use client";

import Breadcrumb from "@/components/ui/Breadcrumb";
import InstagramGrid from "@/components/home/InstagramGrid";
import { Mail, MapPin, Phone } from "lucide-react";

export default function ContactPage() {
    return (
        <main>
            <Breadcrumb title="Contact" />

            <section className="py-20">
                <div className="container mx-auto px-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                        {/* Contact Info */}
                        <div>
                            <div className="mb-12">
                                <h4 className="text-secondary font-bold uppercase mb-4">Contact Info</h4>
                                <p className="text-gray-600 mb-6">
                                    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt cilisis.
                                </p>
                                <div className="space-y-4">
                                    <div className="flex items-start">
                                        <MapPin size={20} className="text-secondary shrink-0 mt-1 mr-4" />
                                        <span className="text-gray-600">1525 Awesome Lane, Los Angeles, CA</span>
                                    </div>
                                    <div className="flex items-start">
                                        <Phone size={20} className="text-secondary shrink-0 mt-1 mr-4" />
                                        <span className="text-gray-600">+1 123 456 7890</span>
                                    </div>
                                    <div className="flex items-start">
                                        <Mail size={20} className="text-secondary shrink-0 mt-1 mr-4" />
                                        <span className="text-gray-600">contact@ashion.com</span>
                                    </div>
                                </div>
                            </div>

                            <div className="mb-12">
                                <h4 className="text-secondary font-bold uppercase mb-4">Send Message</h4>
                                <form className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <input type="text" placeholder="Name" className="border border-gray-300 rounded-full px-6 py-3 focus:outline-none focus:border-primary w-full" />
                                        <input type="email" placeholder="Email" className="border border-gray-300 rounded-full px-6 py-3 focus:outline-none focus:border-primary w-full" />
                                    </div>
                                    <input type="text" placeholder="Website" className="border border-gray-300 rounded-full px-6 py-3 focus:outline-none focus:border-primary w-full" />
                                    <textarea placeholder="Message" rows={4} className="border border-gray-300 rounded-2xl px-6 py-3 focus:outline-none focus:border-primary w-full"></textarea>
                                    <button type="submit" className="bg-primary text-white font-bold uppercase px-8 py-3 rounded-full hover:bg-black transition-colors">
                                        Send Message
                                    </button>
                                </form>
                            </div>
                        </div>

                        {/* Map */}
                        <div className="h-[400px] lg:h-auto bg-gray-200 rounded-lg overflow-hidden">
                            <iframe
                                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d113032.64621395394!2d-118.42775390740968!3d34.02016130939094!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x80c2c75ddc27da13%3A0xe22fdf6f254608f4!2sLos%20Angeles%2C%20CA%2C%20USA!5e0!3m2!1sen!2sbd!4v1584869597033!5m2!1sen!2sbd"
                                className="w-full h-full border-0"
                                allowFullScreen
                                loading="lazy"
                            ></iframe>
                        </div>
                    </div>
                </div>
            </section>

            <InstagramGrid />
        </main>
    );
}
