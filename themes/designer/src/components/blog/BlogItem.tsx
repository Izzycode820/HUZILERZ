"use client";

import Link from "next/link";

interface BlogItemProps {
    image: string;
    title: string;
    date: string;
    author: string;
    excerpt: string;
    commentCount: number;
}

export default function BlogItem({ image, title, date, author, excerpt, commentCount }: BlogItemProps) {
    return (
        <div className="mb-12">
            <div
                className="h-[300px] bg-cover bg-center mb-6 relative"
                style={{ backgroundImage: `url(${image})` }}
            >
            </div>
            <div className="text-xs text-gray-400 uppercase font-medium mb-3 flex items-center space-x-4">
                <span>by {author}</span>
                <span>{date}</span>
                <span>{commentCount} Comments</span>
            </div>
            <h5 className="text-xl font-bold text-secondary mb-3 hover:text-primary transition-colors cursor-pointer">
                <Link href="#">{title}</Link>
            </h5>
            <p className="text-gray-600 mb-4 leading-relaxed">
                {excerpt}
            </p>
            <Link href="#" className="uppercase font-bold text-sm text-secondary hover:text-primary relative after:content-[''] after:absolute after:left-0 after:-bottom-1 after:w-full after:h-[2px] after:bg-primary transition-colors">
                Read more
            </Link>
        </div>
    );
}
