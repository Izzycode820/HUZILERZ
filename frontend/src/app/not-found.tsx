export default function NotFound() {
    return (
        <div style={{
            display: 'flex',
            minHeight: '100vh',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem'
        }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                404 - Page Not Found
            </h2>
            <p style={{ color: '#666' }}>
                The page you're looking for doesn't exist.
            </p>
        </div>
    )
}
