import argparse
import json


def main():
    parser = argparse.ArgumentParser(prog='longbanana')
    commands = parser.add_subparsers(dest='command', required=True)
    validate = commands.add_parser('validate-data', help='Validate hashes, counts, and explicit check bindings')
    validate.add_argument('manifest')
    validate.add_argument('--evaluation', action='store_true')
    for name in ('generate', 'judge', 'judge-direct'):
        run = commands.add_parser(name)
        run.add_argument('--config', required=True)
        run.add_argument('--output', required=True)
        if name in {'judge', 'judge-direct'}:
            run.add_argument('--candidates', required=True)
        run.add_argument('--case', action='append', dest='case_ids')
        run.add_argument('--resume', action='store_true')
        run.add_argument('--dry-run', action='store_true')
        run.add_argument('--shard-index', type=int, default=0)
        run.add_argument('--num-shards', type=int, default=1)
    args = parser.parse_args()
    try:
        if args.command == 'validate-data':
            from .datasets import Dataset
            data = Dataset(args.manifest, args.evaluation)
            result = {'release': data.release, 'fingerprint': data.fingerprint,
                      'counts': data.meta['counts'], 'evaluation_checked': args.evaluation}
        elif args.command == 'judge-direct':
            from .direct import run
            result = run(args.config, args.output, args.candidates, args.resume, args.dry_run,
                         args.case_ids, args.shard_index, args.num_shards)
        else:
            from .supervisor import run
            result = run(args.config, args.command, args.output, getattr(args, 'candidates', None),
                         args.resume, args.dry_run, args.case_ids, args.shard_index, args.num_shards)
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, FileNotFoundError, RuntimeError) as exc:
        # Configuration can include private endpoints. Do not echo it on error.
        parser.exit(2, 'Cannot proceed (' + type(exc).__name__ + '). Check configuration, inputs, and runtime files.\n')


if __name__ == '__main__':
    main()
