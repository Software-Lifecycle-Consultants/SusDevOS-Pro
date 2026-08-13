"""
Migration: Auth Token Tables — PasswordResetTokens, RevokedTokens
App: apps.users
Depends on: apps.users (Users model)

PasswordResetTokens: handles both password-reset flow and new-user onboarding.
  - The same table serves both use cases (TokenType distinguishes them).
  - Raw token is never stored — only a SHA-256 hash.
  - Token expiry: 24h for password reset, 30 days for onboarding.

RevokedTokens: server-side JWT refresh token revocation list.
  - On logout, the refresh token's JTI (JWT ID) is stored here.
  - simplejwt checks this table on each token refresh.
  - A Celery Beat task purges expired entries daily.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_users_roles'),
    ]

    operations = [

        # ── PasswordResetTokens ────────────────────────────────────────────────
        migrations.CreateModel(
            name='PasswordResetTokens',
            fields=[
                ('TokenId', models.AutoField(primary_key=True)),
                ('UserId', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.CASCADE,
                    related_name='password_reset_tokens',
                )),
                ('TokenType', models.PositiveSmallIntegerField(
                    help_text="1: Password Reset (24h expiry), 2: New User Onboarding (30 day expiry)"
                )),
                ('TokenHash', models.CharField(
                    max_length=255,
                    unique=True,
                    help_text="SHA-256 hash of the raw token — never store raw"
                )),
                ('ExpiresAt', models.DateTimeField(
                    help_text="Expiry: +24h for reset, +30 days for onboarding"
                )),
                ('UsedAt', models.DateTimeField(
                    null=True,
                    blank=True,
                    help_text="Populated when token is consumed — prevents reuse"
                )),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('IpAddress', models.CharField(
                    max_length=45,
                    blank=True,
                    null=True,
                    help_text="IP that requested the token (IPv6 compatible)"
                )),
            ],
            options={'db_table': 'password_reset_tokens'},
        ),
        migrations.AddIndex(
            model_name='PasswordResetTokens',
            index=models.Index(fields=['TokenHash'], name='idx_prt_token_hash'),
        ),
        migrations.AddIndex(
            model_name='PasswordResetTokens',
            index=models.Index(fields=['UserId', 'TokenType'], name='idx_prt_user_type'),
        ),

        # ── RevokedTokens ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='RevokedTokens',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                # JTI = JWT ID claim — unique identifier for each refresh token
                ('Jti', models.CharField(
                    max_length=255,
                    unique=True,
                    help_text="JWT ID (jti claim) of the revoked refresh token"
                )),
                ('UserId', models.IntegerField(
                    help_text="User who owned the token (for cleanup queries)"
                )),
                ('RevokedAt', models.DateTimeField(auto_now_add=True)),
                ('ExpiresAt', models.DateTimeField(
                    help_text="Original token expiry — used by cleanup job to prune old rows"
                )),
            ],
            options={'db_table': 'revoked_tokens'},
        ),
        migrations.AddIndex(
            model_name='RevokedTokens',
            index=models.Index(fields=['Jti'], name='idx_revoked_jti'),
        ),
        migrations.AddIndex(
            model_name='RevokedTokens',
            index=models.Index(fields=['ExpiresAt'], name='idx_revoked_expiry'),
        ),
    ]
