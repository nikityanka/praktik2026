function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

export function formatPrice(price) {
    if (typeof price !== 'number') {
        throw new TypeError('Price must be a number');
    }
    return `$${price.toFixed(2)}`;
}