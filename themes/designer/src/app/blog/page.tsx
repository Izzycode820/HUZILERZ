import Breadcrumb from "@/components/ui/Breadcrumb";
import BlogItem from "@/components/blog/BlogItem";
import InstagramGrid from "@/components/home/InstagramGrid";

const blogPosts = [
    {
        image: "/img/blog/blog-1.jpg",
        title: "The Personality Trait That Makes People Happier",
        date: "Seb 17, 2019",
        author: "Seb Robin",
        excerpt: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Risus commodo viverra maecenas accumsan lacus vel facilisis. ",
        commentCount: 6
    },
    {
        image: "/img/blog/blog-2.jpg",
        title: "The Personality Trait That Makes People Happier",
        date: "Seb 17, 2019",
        author: "Seb Robin",
        excerpt: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Risus commodo viverra maecenas accumsan lacus vel facilisis. ",
        commentCount: 6
    },
    {
        image: "/img/blog/blog-3.jpg",
        title: "The Personality Trait That Makes People Happier",
        date: "Seb 17, 2019",
        author: "Seb Robin",
        excerpt: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Risus commodo viverra maecenas accumsan lacus vel facilisis. ",
        commentCount: 6
    },
    {
        image: "/img/blog/blog-4.jpg",
        title: "The Personality Trait That Makes People Happier",
        date: "Seb 17, 2019",
        author: "Seb Robin",
        excerpt: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Risus commodo viverra maecenas accumsan lacus vel facilisis. ",
        commentCount: 6
    },
    {
        image: "/img/blog/blog-5.jpg",
        title: "The Personality Trait That Makes People Happier",
        date: "Seb 17, 2019",
        author: "Seb Robin",
        excerpt: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Risus commodo viverra maecenas accumsan lacus vel facilisis. ",
        commentCount: 6
    },
    {
        image: "/img/blog/blog-6.jpg",
        title: "The Personality Trait That Makes People Happier",
        date: "Seb 17, 2019",
        author: "Seb Robin",
        excerpt: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Quis ipsum suspendisse ultrices gravida. Risus commodo viverra maecenas accumsan lacus vel facilisis. ",
        commentCount: 6
    },
];

export default function BlogPage() {
    return (
        <main>
            <Breadcrumb title="Blog" />

            <section className="py-20">
                <div className="container mx-auto px-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {blogPosts.map((post, index) => (
                            <BlogItem key={index} {...post} />
                        ))}
                    </div>
                    {/* Pagination not explicitly designed but can be added if needed same as Shop */}
                </div>
            </section>

            <InstagramGrid />
        </main>
    );
}
