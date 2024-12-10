FROM rust:1.82-alpine as builder
WORKDIR /usr/src/app
RUN apk add --no-cache \
    musl-dev \
    openssl-dev \
    pkgconfig
COPY . .
RUN cargo build

FROM alpine:edge
COPY --from=builder /usr/src/app/target/release/app /usr/local/bin/app
CMD ["app"]